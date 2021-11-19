<h1>FindTheMag</h1>
FindTheMag helps optimize your BOINC client for gridcoin mining. You can group BOINC projects into two groups: 
"preferred" projects and "mining" projects. Preferred projects are ones which you want to crunch regardless of how much 
GRC they get you. Mining projects are projects which you are willing to crunch, but only if they get you the maximum 
amount of GRC possible. In the event that your preferred project(s) happen to be the most efficient to mine, it will 
assign all project weight to them.

FindTheMag uses your own BOINC client's stats to determine which projects get the most credit per hour on your machine. It then figures out (using your Gridcoin wallet) which project gets you the most magnitude per hour. 

This tool is not perfectly accurate, but accuracy improves the longer you have been running BOINC. It will automatically
set all Gridcoin-approved projects to a weight of one so they will continue to use 1% of your processing power, each
time increasing the accuracy of the tool.

<b>This tool requires that you have the Gridcoin wallet running on your machine</b>. See FAQ for ways around this. The
wallet doesn't need any coins in it, just an up-to-date copy of the blockchain. It also requires python 3.8 or higher,
though earlier versions may work they are unsupported. 

If you use an account manager like BAM:

- Put each host into its own host group
- Assign weight to projects in the host group

If you manage your BOINC client locally:

- There is no way to set project weight outside of logging in to each project manually and setting it there.

If you are a pool miner:

- I don't know the best way to do this, I'll gladly add step-by-step directions here if somebody can provide them.

If you do not have a minimum 1% sidestake setup to the Gridcoin foundation, this program will prompt you to set one up
and refuse to run if you don't. We should all be pitching in to help promote and improve a coin we all benefit from.

If you find this tool useful, consider sidestaking or donating
some GRC to me at RzUgcntbFm8PeSJpauk6a44qbtu92dpw3K

<h3>Quickstart instructions</h3>
For all platforms: Open the first few lines of the file in a text editor and change the settings you want.
<h4>Windows</h4>
<h4>Linux</h4>
<h4>OS X</h4>

<h3>FAQ:</h3>
<b>I'm not getting as many coins as I expect or I haven't received my rewards?</b>

Consult the official Gridcoin help channels, this tool just sets project weights. If you are a solo miner, be sure you
have enabled GDPR export on projects which require it. See https://gridcoin.us/guides/whitelist.htm

<b>My BOINC client doesn't seem to be crunching according to the weight I assigned?</b>

Changing your resource share doesn't insure that your machine will immediately start crunching according to those
resource shares, instead your BOINC client will gradually "catch up". For example, let's say you have a project which
you have recently assigned a weight of "one" to while your other projects add up to 100. Even though 1 is a very small
weight, if you have been crunching for six months and the project previously had a weight of zero, BOINC may fetch a
bunch of work-units to catch up so that it will have crunched that amount of weight over that entire time period. So for
that day, it may appear as if the project has a weight of 1000, but that's because it's average weight is still <1 and
it needs to catch up.

<b>How does it determine the most profitable project?</b>

Each project assigns credit for your work, and BOINC keeps track of how long that work took. The formula to figure out
the profitability of a project is below:

profitability (mag per hour) = (total credits assigned / time those credits took) * mag ratio (average project RAC from
last 30 days / project total magnitude )

<b>Why is it setting all these projects weights to 1?</b>

So that it can gradually accumulate enough stats to determine the profitability of these projects, and so those stats
continue to update as projects change how their applications and credit assignment work.

<b>What if there's a project I <i>never</i> want to crunch?</b>

If you have a grudge against a particular project, you can add it to the ignore list at the top of the script.

<b>What if there is more than one "most profitable" project?</b>

If they are within 10% of each other, project weight will be split evenly between them. This insures crunching will
continue even if one project runs out of work.

<b>Why don't you just say "crunch this project and if there's no work available, crunch this other project?"</b>

Because the BOINC client doesn't have this ability, nor the ability to have projects be in groups. It's open source
though so feel free to contribute to the BOINC project or make your own BOINC Manager clone, this tool could certainly
benefit from it!

<b>What about CPUs or GPUs? Or different applications?</b>

This tool doesn't know about GPUs or different apps, it just calculates an average credits/hour over all work units sent
to you by the project.

<b>How often should I run this?</b>

It's up to you, but it uses a 30-day average to calculate RAC:MAG ratios, so running it very frequently won't get you
much benefit. It's lightweight and doesn't hammer the BOINC project servers though, so feel free to run it as often as
you want!

<b>What are you going to name the pony?</b>

I don't know, current candidates are Jeffrey and Stargazer.

<h3>Advanced Usage</h3>

<b>What if I can't run the Gridcoin wallet on my machine? For example, due to space limitations on my Raspberry Pi?</b>

Then you can copy your BOINC data directory to a machine that has the wallet running and point the script to it.

<h3>Legal</h3>

This software comes with no warranty and is provided as-is. It may crash your computer, it may even steal all your GRC.
Be wise when running software from some random github account.
