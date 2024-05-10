""" This module reads data from a csv file and stores it in a data structure."""
from csv import DictReader

class DataIngestor:
    """Class to ingest data from a csv file and store it in a dictionary"""

    list_of_dict = [] #list of the columns of the csv file
    list_of_states = {} #dictionary of the states and their entries

    def state_entries(self, state):
        """Returns a list of entries for a given state"""
        state_entries = []
        for i in range(len(self.list_of_dict)):
            if self.list_of_dict[i].get("LocationDesc") == state:
                state_entries.append(self.list_of_dict[i])
        return state_entries

    def __init__(self, csv_path: str):
        """Constructor for the DataIngestor"""
        with open(csv_path, 'r', encoding="UTF-8") as file:
            #make a dictionary from the csv file
            dict_reader = DictReader(file)
            #convert the dictionary to a list of dictionaries for each row
            self.list_of_dict = list(dict_reader)

            for i in range(len(self.list_of_dict)):
                if self.list_of_dict[i].get("LocationDesc") not in self.list_of_states:
                    self.list_of_states[self.list_of_dict[i].get("LocationDesc")] = self.state_entries(self.list_of_dict[i].get("LocationDesc"))


        self.questions_best_is_min = [
            'Percent of adults aged 18 years and older who have an overweight classification',
            'Percent of adults aged 18 years and older who have obesity',
            'Percent of adults who engage in no leisure-time physical activity',
            'Percent of adults who report consuming fruit less than one time daily',
            'Percent of adults who report consuming vegetables less than one time daily'
        ]

        self.questions_best_is_max = [
            'Percent of adults who achieve at least 150 minutes a week of moderate-intensity aerobic physical activity or 75 minutes a week of vigorous-intensity aerobic activity (or an equivalent combination)',
            'Percent of adults who achieve at least 150 minutes a week of moderate-intensity aerobic physical activity or 75 minutes a week of vigorous-intensity aerobic physical activity and engage in muscle-strengthening activities on 2 or more days a week',
            'Percent of adults who achieve at least 300 minutes a week of moderate-intensity aerobic physical activity or 150 minutes a week of vigorous-intensity aerobic activity (or an equivalent combination)',
            'Percent of adults who engage in muscle-strengthening activities on 2 or more days a week',
        ]
