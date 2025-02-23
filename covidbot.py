import os
from dotenv import load_dotenv
import requests as rq
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import re
import discord
from discord.ext import commands
import logging
from typing import List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('covid_bot')

class CovidBot(commands.Bot):
    def __init__(self, command_prefix: str):
        intents = discord.Intents.all()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.update_covid_data()
        
    async def setup_hook(self):
        await self.add_cog(CovidCog(self))
        
    def update_covid_data(self):
        """Fetch and process COVID-19 data from disease.sh API"""
        try:
            # Get global data
            global_response = rq.get("https://disease.sh/v3/covid-19/all")
            global_response.raise_for_status()
            self.global_data = global_response.json()
            
            # Get country data
            countries_response = rq.get("https://disease.sh/v3/covid-19/countries")
            countries_response.raise_for_status()
            countries = countries_response.json()
            
            # Process country data
            self.country_data = {
                country['country']: {
                    'TotalConfirmed': country['cases'],
                    'TotalDeaths': country['deaths'],
                    'TotalRecovered': country['recovered'],
                    'CountryCode': country['countryInfo']['iso2']
                }
                for country in countries
            }
            
            logger.info("COVID data updated successfully")
        except Exception as e:
            logger.error(f"Failed to update COVID data: {e}")
            raise

class CovidCog(commands.Cog):
    def __init__(self, bot: CovidBot):
        self.bot = bot
        
    @commands.command()
    async def globalcases(self, ctx):
        """Show global COVID-19 cases"""
        await ctx.send(self.bot.global_data['cases'])
        
    @commands.command()
    async def globalrecovered(self, ctx):
        """Show global COVID-19 recoveries"""
        await ctx.send(self.bot.global_data['recovered'])
        
    @commands.command()
    async def globaldeaths(self, ctx):
        """Show global COVID-19 deaths"""
        await ctx.send(self.bot.global_data['deaths'])
        
    @commands.command()
    async def show(self, ctx, *, country: str):
        """Show COVID-19 statistics for a specific country"""
        try:
            if country not in self.bot.country_data:
                await ctx.send(f"Country '{country}' not found! Please check the country name.")
                return
                
            data = self.bot.country_data[country]
            
            # Create bar chart
            plt.figure(figsize=(10, 6))
            plt.bar(['Cases', 'Deaths', 'Recovered'],
                   [data['TotalConfirmed'], data['TotalDeaths'], data['TotalRecovered']],
                   color=['#FF9999', '#FF0000', '#90EE90'])
            plt.title(f"COVID-19 Statistics for {country}")
            plt.ylabel("Number of Cases")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.savefig('covid_stats.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Create embed
            embed = discord.Embed(
                title=country,
                description='Current COVID-19 Statistics',
                colour=discord.Colour.blue()
            )
            
            embed.set_footer(text="Data source: disease.sh | Stay Safe!")
            embed.add_field(name='Total Cases', value=f"{data['TotalConfirmed']:,}", inline=False)
            embed.add_field(name='Total Deaths', value=f"{data['TotalDeaths']:,}", inline=False)
            embed.add_field(name='Total Recovered', value=f"{data['TotalRecovered']:,}", inline=False)
            
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File('covid_stats.png'))
            
        except Exception as e:
            logger.error(f"Error in show command: {e}")
            await ctx.send("An error occurred while processing your request.")
            
    @commands.command()
    async def compare(self, ctx, *, countries: str):
        """Compare COVID-19 cases between two countries (format: Country1-Country2)"""
        try:
            country1, country2 = countries.split('-')
            country1 = country1.strip()
            country2 = country2.strip()
            
            if country1 not in self.bot.country_data or country2 not in self.bot.country_data:
                await ctx.send("One or both countries not found! Please check the country names.")
                return
                
            cases = [
                self.bot.country_data[country1]['TotalConfirmed'],
                self.bot.country_data[country2]['TotalConfirmed']
            ]
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar([country1, country2], cases, color=['#FF9999', '#FF9999'])
            plt.title(f"COVID-19 Cases Comparison")
            plt.ylabel("Number of Cases")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:,.0f}',
                        ha='center', va='bottom')
            
            plt.savefig('comparison.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            embed = discord.Embed(
                title='COVID-19 Cases Comparison',
                description='Current Statistics',
                colour=discord.Colour.blue()
            )
            
            embed.set_footer(text="Data source: disease.sh | Stay Safe!")
            embed.add_field(name=country1, value=f"{cases[0]:,}", inline=True)
            embed.add_field(name=country2, value=f"{cases[1]:,}", inline=True)
            
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File('comparison.png'))
            
        except ValueError:
            await ctx.send("Please use the format: !compare Country1-Country2")
        except Exception as e:
            logger.error(f"Error in compare command: {e}")
            await ctx.send("An error occurred while processing your request.")

    @commands.command()
    async def topcases(self, ctx, limit: int = 5):
        """Show countries with the highest number of cases"""
        try:
            sorted_countries = sorted(
                self.bot.country_data.items(),
                key=lambda x: x[1]['TotalConfirmed'],
                reverse=True
            )[:limit]
            
            countries = [country for country, _ in sorted_countries]
            cases = [data['TotalConfirmed'] for _, data in sorted_countries]
            
            plt.figure(figsize=(12, 6))
            bars = plt.bar(countries, cases, color='#FF9999')
            plt.title(f"Top {limit} Countries by COVID-19 Cases")
            plt.ylabel("Number of Cases")
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:,.0f}',
                        ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig('top_cases.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            embed = discord.Embed(
                title=f"Top {limit} Countries by COVID-19 Cases",
                description='Current Statistics',
                colour=discord.Colour.blue()
            )
            
            for country, data in sorted_countries:
                embed.add_field(
                    name=country,
                    value=f"{data['TotalConfirmed']:,} cases",
                    inline=False
                )
            
            embed.set_footer(text="Data source: disease.sh | Stay Safe!")
            
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File('top_cases.png'))
            
        except Exception as e:
            logger.error(f"Error in topcases command: {e}")
            await ctx.send("An error occurred while processing your request.")

    @commands.command()
    async def mortality(self, ctx, *, country: str):
        """Show mortality rate for a specific country"""
        try:
            if country not in self.bot.country_data:
                await ctx.send(f"Country '{country}' not found! Please check the country name.")
                return
                
            data = self.bot.country_data[country]
            mortality_rate = (data['TotalDeaths'] / data['TotalConfirmed'] * 100) if data['TotalConfirmed'] > 0 else 0
            
            embed = discord.Embed(
                title=f"COVID-19 Mortality Rate - {country}",
                description='Current Statistics',
                colour=discord.Colour.blue()
            )
            
            embed.add_field(name='Total Cases', value=f"{data['TotalConfirmed']:,}", inline=True)
            embed.add_field(name='Total Deaths', value=f"{data['TotalDeaths']:,}", inline=True)
            embed.add_field(name='Mortality Rate', value=f"{mortality_rate:.2f}%", inline=False)
            
            embed.set_footer(text="Data source: disease.sh | Stay Safe!")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in mortality command: {e}")
            await ctx.send("An error occurred while processing your request.")

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("No Discord token found in .env file. Please check your .env file contains DISCORD_TOKEN.")
        return
        
    try:
        bot = CovidBot(command_prefix='!')
        logger.info("Starting bot...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()