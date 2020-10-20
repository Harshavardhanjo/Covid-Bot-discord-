import requests as rq
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import re

import discord
from discord.ext import commands



client = commands.Bot(command_prefix = '!')



#data gets

data2 = rq.get("https://api.covid19api.com/summary")
r = data2.json()

#data gets



#data analyse

d = list(r.values())
glb = dict(d[0])
glbkeys = list(glb.keys())
glbvalues = list(glb.values())
a = list(d[1])
b = list(d[2])

i = 0
index = 0


globalconf = 0
globalrec = 0
globaldeaths = 0

totconf =  []
totdeaths = []
totrec = []
country = []
countrycode = []

while(i<len(b)):
	country.append(b[i]['Country'])
	totconf.append(b[i]['TotalConfirmed'])
	countrycode.append(b[i]['CountryCode'])
	totrec.append(b[i]['TotalRecovered'])
	totdeaths.append(b[i]['TotalDeaths'])
	i += 1


for i in totconf:
	globalconf += i

for i in totdeaths:
	globaldeaths += i

for i in totrec:
	globalrec += i

df = pd.DataFrame([totconf,totdeaths,totrec,'0']).T
df.columns = ['Country','totconf','totdeaths','totrec']
df.index = [country]






@client.event
async def on_ready():
	print("I am ready")

@client.command()
async def globalcases(ctx):
    await ctx.send(globalconf)

@client.command()
async def globalrecovered(ctx):
    await ctx.send(globalrec)

@client.command()
async def globaldeaths(ctx):
    await ctx.send(globaldeaths)

@client.command()
async def show(ctx,arg):

	index = 0

	for i in country:

		if(i == arg):

			#await ctx.send(i)

			#await ctx.send(f'     CASES : {totconf[index]}')
			#await ctx.send(f'     DEATHS : {totdeaths[index]}')
			#await ctx.send(f'     RECOVERED : {totrec[index]}')

			temp = []
			temp.append(totconf[index])
			temp.append(totdeaths[index])
			temp.append(totrec[index])

			plt.bar(['Cases','Deaths','Recovered'],temp)
			plt.savefig('foo.png', dpi=600, format='png')

			embed = discord.Embed(

			title = i,
			description = 'Live Current Data',
			colour = discord.Colour.blue()


			)

			embed.set_footer(text = "STAY SAFE!")
			embed.add_field(name = 'Country', value = i, inline = False)
			embed.add_field(name = 'Total Cases', value = totconf[index], inline = False)
			embed.add_field(name = 'Total Deaths', value = totdeaths[index], inline = False)
			embed.add_field(name = 'Total Recovered', value = totrec[index], inline = False)






		index += 1

	await ctx.send(embed = embed)
	await ctx.send(file=discord.File('foo.png'))







@client.command()
async def ping(ctx):
    await ctx.send(f'pong {round(client.latency*1000)}ms')

@client.command()
async def compare(ctx,arg):

	c = re.split('-',arg)

	cmp = []

	index = 0

	for i in country:

		if(i == c[0]):

			cmp.append(totconf[index])

		index += 1

	index = 0

	for i in country:

		if(i == c[1]):

			cmp.append(totconf[index])

	index += 1


	plt.bar(c,cmp)
	plt.savefig('image.png', dpi=600, format='png')
	plt.clf()

	embed = discord.Embed(
	title = 'Compared Result',
	description = 'Live Current Data',
	colour = discord.Colour.blue()

	)

	embed.set_footer(text = "STAY SAFE!")
	embed.add_field(name = 'Country 1', value = c[0], inline = True)
	embed.add_field(name = 'Country 2', value = c[1], inline = True)
	embed.add_field(name = 'Cases 1', value = cmp[0], inline = False)
	embed.add_field(name = 'Cases 2', value = cmp[1], inline = False)



	await ctx.send(embed = embed)
	await ctx.send(file=discord.File('image.png'))








client.run('your key here')
