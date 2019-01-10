'''
Grab latest F1 results.
'''

# -- Use caching for all requests to reuse results from previous command use, only request directly from API if expired --
# -- Check if race weekend, lower cache period --
# !f1 -- return all driver and constructor standings as table/embed
# !f1 wdc | drivers -- only drivers
# !f1 <driverName> -- race wins and poles for driver
# !f1 wcc | constructors -- only constructors
# !f1 <constructor> -- constructor points
# !f1 calendar | races -- all race weekends, ciruits, dates
# !f1 countdown | next -- next race circuit, weekend, date and countdown timer
# !f1 update -- ADMIN, manually reset cache
# !f1 help | <command> help -- help text and usage example
