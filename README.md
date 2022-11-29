# VacationSelection

This script has been created to help automate vacation requests and approval/denial of the most popular vacation/holidays for the TCESD2 Crew Members.
Notes kept in mind for selection process:

- Each member may pick a maximum of 18 days, or as few as 0 
    - Drafts will prioritize Seniority
    - in the case of multiple members starting on the same day, each members will be shuffled randomly
    - Each member shall be approved 2 days before moving on to the next member
    - unless all requested days have been addressed
    - If a day is denied, their next pick will be automatically considered until either 2 days have been approved, or the pick list is empty
    - Only 5 members may request off for any given day
    - 6th and further will be automatically denied.

## Data Location

- Data is gathered via jotform [https://form.jotform.com/223213539120040](https://form.jotform.com/223213539120040)
- And can be viewed at [https://docs.google.com/spreadsheets/d/1a9t628BOgbaXZikIHMEOYbJVbG4gTbkJECGNl7knylo/edit#gid=345096181](https://docs.google.com/spreadsheets/d/1a9t628BOgbaXZikIHMEOYbJVbG4gTbkJECGNl7knylo/edit#gid=345096181)

## Running

- Save the final results file as a CSV file
- run python script (TO DO)
- output CSV will be created (TO DO)

### TODO: Randomize order each run for those sharing the same hire date

assign each firefighter a random number while creating their FFighter Object (dice):
priority order can then be calculated as 1) HireDate 2) dice
