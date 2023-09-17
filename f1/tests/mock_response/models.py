"""Model response data for mock API tests."""


def standings_wrapper(body):
    """Helper wraps `body` XML string in <StandingsTable> and <StandingsList> tags."""
    return f'''
        <StandingsTable season="2018">
            <StandingsList season="2018" round="21">
                {body}
            </StandingsList>
        </StandingsTable>'''


def result_wrapper(body, quali=False):
    """Wraps `body` XML string in parent <RaceTable><ResultsList> and <Race> tags.

    If `quali` is True <ResultsList> is replaced with <QualifyingList>.
    """
    if quali is True:
        wrapper = f'''<QualifyingList>{body}</QualifyingList>'''
    else:
        wrapper = f'''<ResultsList>{body}</ResultsList>'''
    return f'''
        <RaceTable season="2018" round="21">
            <Race season="2018" round="21" url="https://en.wikipedia.org/wiki/2018_Abu_Dhabi_Grand_Prix">
                <RaceName>Abu Dhabi Grand Prix</RaceName>
                <Circuit circuitId="yas_marina" url="http://en.wikipedia.org/wiki/Yas_Marina_Circuit">
                    <CircuitName>Yas Marina Circuit</CircuitName>
                    <Location lat="24.4672" long="54.6031">
                        <Locality>Abu Dhabi</Locality>
                        <Country>UAE</Country>
                    </Location>
                </Circuit>
                <Date>2018-11-25</Date>
                <Time>13:10:00Z</Time>
                {wrapper}
            </Race>
        </RaceTable>'''


driver_standings = standings_wrapper('''
    <DriverStanding position="1" positionText="1" points="408" wins="11">
        <Driver driverId="hamilton" code="HAM" url="http://en.wikipedia.org/wiki/Lewis_Hamilton">
            <PermanentNumber>44</PermanentNumber>
            <GivenName>Lewis</GivenName>
            <FamilyName>Hamilton</FamilyName>
            <DateOfBirth>1985-01-07</DateOfBirth>
            <Nationality>British</Nationality>
        </Driver>
        <Constructor constructorId="mercedes" url="http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One">
            <Name>Mercedes</Name>
            <Nationality>German</Nationality>
        </Constructor>
    </DriverStanding>''')

constructor_standings = standings_wrapper('''
    <ConstructorStanding position="1" positionText="1" points="655" wins="11">
        <Constructor constructorId="mercedes" url="http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One">
            <Name>Mercedes</Name>
            <Nationality>German</Nationality>
        </Constructor>
    </ConstructorStanding>''')

driver_info_xml = '''
    <DriverTable driverId="alonso">
        <Driver driverId="alonso" code="ALO" url="http://en.wikipedia.org/wiki/Fernando_Alonso">
            <PermanentNumber>14</PermanentNumber>
            <GivenName>Fernando</GivenName>
            <FamilyName>Alonso</FamilyName>
            <DateOfBirth>1981-07-29</DateOfBirth>
            <Nationality>Spanish</Nationality>
        </Driver>
    </DriverTable>'''

driver_info_json = {
    "MRData": {
        "DriverTable": {
            "Drivers": [
                {
                    "driverId": "alonso",
                    "permanentNumber": "14",
                    "code": "ALO",
                    "url": "http:\/\/en.wikipedia.org\/wiki\/Fernando_Alonso",
                    "givenName": "Fernando",
                    "familyName": "Alonso",
                    "dateOfBirth": "1981-07-29",
                    "nationality": "Spanish"
                }
            ]
        }
    }
}

race_schedule = '''
    <RaceTable season="2018">
        <Race season="2018" round="1" url="https://en.wikipedia.org/wiki/2018_Australian_Grand_Prix">
            <RaceName>Australian Grand Prix</RaceName>
            <Circuit circuitId="albert_park" url="http://en.wikipedia.org/wiki/Melbourne_Grand_Prix_Circuit">
                <CircuitName>Albert Park Grand Prix Circuit</CircuitName>
                <Location lat="-37.8497" long="144.968">
                    <Locality>Melbourne</Locality>
                    <Country>Australia</Country>
                </Location>
            </Circuit>
            <Date>2018-03-25</Date>
            <Time>05:10:00Z</Time>
        </Race>
        <Race season="2018" round="2" url="https://en.wikipedia.org/wiki/2018_Bahrain_Grand_Prix">
            <RaceName>Bahrain Grand Prix</RaceName>
            <Circuit circuitId="bahrain" url="http://en.wikipedia.org/wiki/Bahrain_International_Circuit">
                <CircuitName>Bahrain International Circuit</CircuitName>
                <Location lat="26.0325" long="50.5106">
                    <Locality>Sakhir</Locality>
                    <Country>Bahrain</Country>
                </Location>
            </Circuit>
            <Date>2018-04-08</Date>
            <Time>15:10:00Z</Time>
        </Race>
    </RaceTable>'''

race_results = result_wrapper('''
    <ResultsList>
        <Result number="44" position="1" positionText="1" points="25">
            <Driver driverId="hamilton" code="HAM" url="http://en.wikipedia.org/wiki/Lewis_Hamilton">
                <PermanentNumber>44</PermanentNumber>
                <GivenName>Lewis</GivenName>
                <FamilyName>Hamilton</FamilyName>
                <DateOfBirth>1985-01-07</DateOfBirth>
                <Nationality>British</Nationality>
            </Driver>
            <Constructor constructorId="mercedes" url="http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One">
                <Name>Mercedes</Name>
                <Nationality>German</Nationality>
            </Constructor>
            <Grid>1</Grid>
            <Laps>55</Laps>
            <Status statusId="1">Finished</Status>
            <Time millis="5980382">1:39:40.382</Time>
            <FastestLap rank="5" lap="53">
                <Time>1:41.357</Time>
                <AverageSpeed units="kph">197.267</AverageSpeed>
            </FastestLap>
        </Result>
    </ResultList>''')

qualifying_results = result_wrapper('''
    <QualifyingResult number="44" position="1">
        <Driver driverId="hamilton" code="HAM" url="http://en.wikipedia.org/wiki/Lewis_Hamilton">
            <PermanentNumber>44</PermanentNumber>
            <GivenName>Lewis</GivenName>
            <FamilyName>Hamilton</FamilyName>
            <DateOfBirth>1985-01-07</DateOfBirth>
            <Nationality>British</Nationality>
        </Driver>
        <Constructor constructorId="mercedes" url="http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One">
            <Name>Mercedes</Name>
            <Nationality>German</Nationality>
        </Constructor>
        <Q1>1:36.828</Q1>
        <Q2>1:35.693</Q2>
        <Q3>1:34.794</Q3>
    </QualifyingResult>
    <QualifyingResult number="77" position="2">
        <Driver driverId="bottas" code="BOT" url="http://en.wikipedia.org/wiki/Valtteri_Bottas">
            <PermanentNumber>77</PermanentNumber>
            <GivenName>Valtteri</GivenName>
            <FamilyName>Bottas</FamilyName>
            <DateOfBirth>1989-08-28</DateOfBirth>
            <Nationality>Finnish</Nationality>
        </Driver>
        <Constructor constructorId="mercedes" url="http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One">
            <Name>Mercedes</Name>
            <Nationality>German</Nationality>
        </Constructor>
        <Q1>1:36.789</Q1>
        <Q2>1:36.392</Q2>
        <Q3>1:34.956</Q3>
    </QualifyingResult>''', quali=True)

driver_wins = result_wrapper('''
    <Result number="8" position="1" positionText="1" points="10">
        <Driver driverId="alonso" code="ALO" url="http://en.wikipedia.org/wiki/Fernando_Alonso">
            <PermanentNumber>14</PermanentNumber>
            <GivenName>Fernando</GivenName>
            <FamilyName>Alonso</FamilyName>
            <DateOfBirth>1981-07-29</DateOfBirth>
            <Nationality>Spanish</Nationality>
        </Driver>
        <Constructor constructorId="renault" url="http://en.wikipedia.org/wiki/Renault_in_Formula_One">
            <Name>Renault</Name>
            <Nationality>French</Nationality>
        </Constructor>
        <Grid>1</Grid>
        <Laps>70</Laps>
        <Status statusId="1">Finished</Status>
        <Time millis="5941460">1:39:01.460</Time>
    </Result>''')

driver_poles = result_wrapper('''
    <QualifyingResult number="8" position="1">
        <Driver driverId="alonso" code="ALO" url="http://en.wikipedia.org/wiki/Fernando_Alonso">
            <PermanentNumber>14</PermanentNumber>
            <GivenName>Fernando</GivenName>
            <FamilyName>Alonso</FamilyName>
            <DateOfBirth>1981-07-29</DateOfBirth>
            <Nationality>Spanish</Nationality>
        </Driver>
        <Constructor constructorId="renault" url="http://en.wikipedia.org/wiki/Renault_in_Formula_One">
            <Name>Renault</Name>
            <Nationality>French</Nationality>
        </Constructor>
        <Q1>1:37.044</Q1>
    </QualifyingResult>''', quali=True)

driver_championships = standings_wrapper('''
    <DriverStanding position="1" positionText="1" points="133" wins="7">
        <Driver driverId="alonso" code="ALO" url="http://en.wikipedia.org/wiki/Fernando_Alonso">
            <PermanentNumber>14</PermanentNumber>
            <GivenName>Fernando</GivenName>
            <FamilyName>Alonso</FamilyName>
            <DateOfBirth>1981-07-29</DateOfBirth>
            <Nationality>Spanish</Nationality>
        </Driver>
        <Constructor constructorId="renault" url="http://en.wikipedia.org/wiki/Renault_in_Formula_One">
            <Name>Renault</Name>
            <Nationality>French</Nationality>
        </Constructor>
    </DriverStanding>''')

driver_teams = '''
    <ConstructorTable driverId="alonso">
        <Constructor constructorId="ferrari" url="http://en.wikipedia.org/wiki/Scuderia_Ferrari">
            <Name>Ferrari</Name>
            <Nationality>Italian</Nationality>
        </Constructor>
    </ConstructorTable>'''

all_standings_for_driver = ('''
    <StandingsTable driverId="alonso">
        <StandingsList season="2004" round="18">
            <DriverStanding position="4" positionText="4" points="59" wins="0">
                <Driver driverId="alonso" code="ALO" url="http://en.wikipedia.org/wiki/Fernando_Alonso">
                    <PermanentNumber>14</PermanentNumber>
                    <GivenName>Fernando</GivenName>
                    <FamilyName>Alonso</FamilyName>
                    <DateOfBirth>1981-07-29</DateOfBirth>
                    <Nationality>Spanish</Nationality>
                </Driver>
                <Constructor constructorId="renault" url="https://en.wikipedia.org/wiki/Renault_in_Formula_One">
                    <Name>Renault</Name>
                    <Nationality>French</Nationality>
                </Constructor>
            </DriverStanding>
        </StandingsList>
        <StandingsList season="2005" round="19">
            <DriverStanding position="1" positionText="1" points="133" wins="7">
                <Driver driverId="alonso" code="ALO" url="http://en.wikipedia.org/wiki/Fernando_Alonso">
                    <PermanentNumber>14</PermanentNumber>
                    <GivenName>Fernando</GivenName>
                    <FamilyName>Alonso</FamilyName>
                    <DateOfBirth>1981-07-29</DateOfBirth>
                    <Nationality>Spanish</Nationality>
                </Driver>
                <Constructor constructorId="renault" url="https://en.wikipedia.org/wiki/Renault_in_Formula_One">
                    <Name>Renault</Name>
                    <Nationality>French</Nationality>
                </Constructor>
            </DriverStanding>
        </StandingsList>
        <StandingsList season="2006" round="18">
            <DriverStanding position="1" positionText="1" points="134" wins="7">
                <Driver driverId="alonso" code="ALO" url="http://en.wikipedia.org/wiki/Fernando_Alonso">
                    <PermanentNumber>14</PermanentNumber>
                    <GivenName>Fernando</GivenName>
                    <FamilyName>Alonso</FamilyName>
                    <DateOfBirth>1981-07-29</DateOfBirth>
                    <Nationality>Spanish</Nationality>
                </Driver>
                <Constructor constructorId="renault" url="https://en.wikipedia.org/wiki/Renault_in_Formula_One">
                    <Name>Renault</Name>
                    <Nationality>French</Nationality>
                </Constructor>
            </DriverStanding>
        </StandingsList>
    </StandingsTable>
''')

all_laps = result_wrapper('''
    <LapsList>
        <Lap number="1">
            <Timing driverId="alonso" lap="1" position="1" time="1:34.494"/>
            <Timing driverId="vettel" lap="1" position="2" time="1:34.294"/>
        </Lap>
        <Lap number="2">
            <Timing driverId="alonso" lap="2" position="2" time="1:30.612"/>
            <Timing driverId="vettel" lap="2" position="1" time="1:34.194"/>
        </Lap>
    </LapsList>''')

driver1_laps = result_wrapper('''
    <LapsList>
        <Lap number="1">
            <Timing driverId="alonso" lap="1" position="1" time="1:34.494"/>
        </Lap>
        <Lap number="2">
            <Timing driverId="alonso" lap="2" position="1" time="1:30.812"/>
        </Lap>
        <Lap number="3">
            <Timing driverId="alonso" lap="3" position="1" time="1:30.606"/>
        </Lap>
        <Lap number="4">
            <Timing driverId="alonso" lap="4" position="1" time="1:30.012"/>
        </Lap>
        <Lap number="5">
            <Timing driverId="alonso" lap="5" position="1" time="1:30.318"/>
        </Lap>
    </LapsList>''')

driver2_laps = result_wrapper('''
    <LapsList>
        <Lap number="1">
            <Timing driverId="vettel" lap="1" position="1" time="1:34.194"/>
        </Lap>
        <Lap number="2">
            <Timing driverId="vettel" lap="2" position="1" time="1:30.512"/>
        </Lap>
        <Lap number="3">
            <Timing driverId="vettel" lap="3" position="1" time="1:30.806"/>
        </Lap>
        <Lap number="4">
            <Timing driverId="vettel" lap="4" position="1" time="1:29.912"/>
        </Lap>
        <Lap number="5">
            <Timing driverId="vettel" lap="5" position="1" time="1:29.718"/>
        </Lap>
    </LapsList>''')

pitstops = result_wrapper('''
    <PitStopsList>
        <PitStop driverId="alonso" stop="1" lap="1" time="17:16:20" duration="41.012"/>
        <PitStop driverId="alonso" stop="2" lap="7" time="17:29:33" duration="21.283"/>
        <PitStop driverId="alonso" stop="3" lap="15" time="17:44:11" duration="22.630"/>
    </PitStopsList>''')


driver_seasons = ('''
    <SeasonTable driverId="alonso">
        <Season url="https://en.wikipedia.org/wiki/2001_Formula_One_season">2001</Season>
    </SeasonTable>''')

# All drivers and teams is taken from driver standings results
grid = driver_standings

# Model for testing rank_best_lap_times()
best_laps = {
    'data': [
        {
            'Rank': 1,
            'Time': '1:30.202',
        },
        {
            'Rank': 2,
            'Time': '1:29.200',
        },
        {
            'Rank': 3,
            'Time': '1:29:190',
        },
        {
            'Rank': 4,
            'Time': '1:29.150',
        },
        {
            'Rank': 5,
            'Time': '1:28.100',
        },
        {
            'Rank': 6,
            'Time': '1:28.100',
        },
        {
            'Rank': 7,
            'Time': '1:28.100',
        }
    ]
}

all_drivers = {
    "MRData": {
        "DriverTable": {
            "Drivers": [
                {
                    "driverId": "alonso",
                    "permanentNumber": "14",
                    "code": "ALO",
                    "url": "http:\/\/en.wikipedia.org\/wiki\/Fernando_Alonso",
                    "givenName": "Fernando",
                    "familyName": "Alonso",
                    "dateOfBirth": "1981-07-29",
                    "nationality": "Spanish"
                },
                {
                    "driverId": "max_verstappen",
                    "permanentNumber": "1",
                    "code": "VER",
                    "url": "http:\/\/en.wikipedia.org\/wiki\/Max_Verstappen",
                    "givenName": "Max",
                    "familyName": "Verstappen",
                    "dateOfBirth": "1981-07-29",
                    "nationality": "Dutch"
                }
            ]
        }
    }
}
