# FindTheMag
FindTheMag helps optimize your BOINC client for gridcoin mining. You can group BOINC projects into two groups: 
"preferred" projects and "mining" projects. Preferred projects are ones which you want to crunch regardless of how much 
GRC they get you. Mining projects are projects which you are willing to crunch, but only if they get you the maximum 
amount of GRC possible. In the event that your preferred project(s) happen to be the most efficient to mine, it will 
assign all project weight to them.

FindTheMag uses your own BOINC client's stats to determine which projects get the most credit per hour on your machine. It then figures out (using your Gridcoin wallet) which project gets you the most magnitude per hour. [Quickmag](http://quickmag.ml/cgi-bin/script.cgi) is a similar tool which will estimate the most profitable projects for your hardware based on the performance of other crunchers with similar hardware.

This tool's accuracy improves the longer you have been running BOINC. It will automatically set all Gridcoin-approved 
projects to a weight of one so they will continue to use .1% of your processing power, each time increasing the accuracy of the tool.

<b>This tool requires that you have the Gridcoin wallet running on your machine</b> and that it is fully synced. See FAQ for ways around this. The
wallet doesn't need any coins in it, just an up-to-date copy of the blockchain. It also requires python 3.8 or higher,
though earlier versions may work they are unsupported. If you just installed BOINC, this tool takes about 48 hours to start working as we have to wait for projects to grant you credit for your work.

<b>If you use an account manager like BAM:</b>

- Put each host into its own host group
- Assign weight to projects in the host group

<b>If you manage your BOINC client locally:</b>

- There is no way to set project weight outside of logging in to each project manually and setting it there.

<b>If you are a pool miner:</b>

- I don't know the best way to do this, I'll gladly add step-by-step directions here if somebody can provide them. I would assume it works similarly to BAM.

If you do not have a minimum 1% sidestake setup to the Gridcoin foundation, this program will prompt you to set one up
and refuse to run if you don't. We should all be pitching in to help promote and improve a coin we all benefit from.

If you find this tool useful, consider sidestaking or donating
some GRC to me at RzUgcntbFm8PeSJpauk6a44qbtu92dpw3K

## Quickstart instructions
For all platforms: Open the first few lines of the main.py file in a text editor and change the settings you want.
<h4>Windows</h4>
 - No step by step available yet

<h4>Linux</h4>

 - Open a terminal and go to the folder you downloaded this tool into using `cd /home/user/Downloads/FindTheMag` or wherever you put it
 - Run `pip3 install -r requirements.txt` (Note that you need pip installed, if you don't have it, you might need to run a `sudo apt install python3-pip`)
 - Run `python3 main.py`

<h4>OS X</h4>

 - Open a terminal and go to the folder you downloaded this tool into using `cd /home/user/Downloads/FindTheMag` or wherever you put it
 - Run `pip3 install -r requirements.txt`
 - Run `python3 main.py`

### FAQ:
<b>I'm not getting as many coins as I expect or I haven't received my rewards?</b>

Consult the official Gridcoin help channels, this tool just suggests project weights. If you are a solo miner, be sure you
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

First it calculates the mag ratio: 

mag ratio =  project total magnitude / average total project RAC from last 30 days

Then you can get profitability (mag/hr): 

profitability = (total credits earned / time those credits took) * mag ratio 

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

<b>What does "The following projects do not have enough stats to be calculated accurately" mean?</b>

It means you have completed less than 10 tasks for this project. At ten tasks, under ideal circumstances, we could get within 10% of the correct "credits per hour" estimation which is needed to determine mag per hour. So if less than 10 WUs have been completed, we don't even try to make an estimate.

<h3>Advanced Usage</h3>

<b>What if I can't run the Gridcoin wallet on my machine? For example, due to space limitations on my Raspberry Pi?</b>

Then you can copy your BOINC data directory to a machine that has the wallet running and point the script to it. Note that you don't need to copy any subfolders in the BOINC directory, just the root directory and files directly beneath it.

<h3>Legal</h3>

- This software comes with no warranty and is provided as-is. Be wise when running software from some random github account. It may calculate suggested weights wrong. It may crash your computer, it may even steal all your GRC. By using it, you agree to hold the developers harmless for any damage it may cause whether through negligence, accident, or malice to the fullest extent legally possible. You also agree to allow yourself to have a wonderful day today or you are not allowed to use this software.
- If you submit any or pull requests to this repository or its developer, you agree to have the code ownership transferred to the repository owner and licensed under the same license as the other code in the repository is licensed under.
- This software is produced independently of the Gridcoin and BOINC projects without their approval or endorsement.

