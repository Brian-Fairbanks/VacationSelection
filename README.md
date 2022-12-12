# VacationSelection

This script has been created to help automate vacation requests and approval/denial of the most popular vacation/holidays for the TCESD2 Crew Members.

Notes kept in mind for selection process:

a _pick_ shall be defined as a prefered day each fire fighter would like to take off.

- Each member may 'pick' a maximum of 18 days, or as few as 0, in order of preferece
- Each members picks shall be addressed in a draft of 2 approved days before moving on to the next member
  - unless all of a members picks have been addressed
  - If a pick is denied for any reason, their next pick will be automatically considered until either 2 days have been approved, or the pick list is empty
- Drafts will prioritize Seniority
  - in the case of multiple members sharing seniority (starting on the same day), member will be shuffled randomly for EACH draft of 2 picks

As per _**Daily Staffing** - OPS 001-01_

- Only 5 members may request off for any given day
- Of those 5, there can be:
  - No more than 3 Lieutenants
  - No more than 2 Captains / Battalion Chief
  - No more than 3 Apparatus Specialists

## Data Location

- Data is gathered via jotform:
  - [https://form.jotform.com/223213539120040](https://form.jotform.com/223213539120040)
- And can be viewed at:
  - [https://docs.google.com/spreadsheets/d/1a9t628BOgbaXZikIHMEOYbJVbG4gTbkJECGNl7knylo/edit#gid=345096181](https://docs.google.com/spreadsheets/d/1a9t628BOgbaXZikIHMEOYbJVbG4gTbkJECGNl7knylo/edit#gid=345096181)

## Running

- Save the final results file as a CSV file
- run python script (TO DO)
- output CSV will be created (TO DO)

## Randomization:

As each person is added to memory, it assigns them a random float (essentially zero through one Quintillion)
It then orders by seniority first, and the random number second.

![randomization demonstration](https://github.com/Brian-Fairbanks/VacationSelection/blob/main/readme/Randomization.gif?raw=true)

You can see in the gif that each time I click, it reruns
The list stays generally the same, but you can see a few people shuffle around. The easiest to catch are
(lists bellow are pulled from the last run)

- The first 2:

```
  Cunnningham, R : 1998-02-01 - 0.11728346733719786
  Randazzo, D : 1998-02-01 - 0.7968179167790319
```

- 10th through 2nd to last:

```
  Neely, W : 2022-01-17 - 0.011172286367265194
  Luckie, H : 2022-01-17 - 0.026730481744500656
  Patton, A : 2022-01-17 - 0.09485427132878543
  Arteaga, B : 2022-01-17 - 0.4718491504172233
  Brindle, N : 2022-01-17 - 0.6241731795673027
  Nutting, P : 2022-01-17 - 0.6256747046059348
  Harris, T : 2022-01-17 - 0.8317098147199816
  De Luna, J : 2022-01-17 - 0.8323556134197091
  Finn, K : 2022-01-17 - 0.9165516986359395
```

## TODO:

- seperate drafts by shift
- add file picker to start (or google api to auto-read from from sheets?)
- prevent time picks without type
- prevent one person from submitting multiple forms

- BC and Captains cant take off on the same days past a certain point
  - get exact details

## Done:

- re-randomize after every set

  - print total array for each cycle

- output to CSV format
