""" @package appInfo
This program proposes a method to compute similarity score between two itunes applications.
"""
from __future__ import division  # to maximize portability between python 2.7 and 3.5
import sys

if sys.version_info < (3, 5):
    import urllib2
else:
    import urllib
    import urllib.request
import json
import difflib
from multiprocessing import Pool

__author__ = "Kunal Khanna"
__license__ = "GPL"
__version__ = "0.1"
__email__ = "ccepl.kunal@gmail.com"


class AppInfo:
    def __init__(self, Primary, Secondary):
        """
        Constructor method
        :param Primary: Primary app_id
        :param Secondary: list of Secondary app_id
        """
        try:
            assert len(Primary), "Primary String is Empty"
            assert len(Secondary), "Primary list is Empty"

            self._Primary_app_info = dict()
            self._Secondary_app_info = list(dict())
            self._Primary = Primary
            self._Secondary = Secondary
        except AssertionError as e:
            print("Error: _init_ %s" % e)
            sys.exit("Exit script with error code %s" % e)
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)
            sys.exit("Exit script with error code %s" % e)

    @staticmethod
    def _fetch_app_info(app_id):
        """
        method to fetch app info from set lookup url in json format and convert to dict format
        :param app_id: app_id parameter for lookup query
        :return app_info: dict converted json app info
        """
        try:
            assert len(app_id), "Empty string"
            lookup_url = "https://itunes.apple.com/lookup?id="
            target_url = lookup_url + app_id
            if sys.version_info < (3, 5):
                response = urllib2.urlopen(target_url)
            else:
                response = urllib.request.urlopen(target_url)
            data = response.read()  # a `bytes` object
            text = data.decode('utf-8')
            app_info = json.loads(text)
            return app_info
        except AssertionError as e:
            print(e)
            sys.exit("Exit script with error code %s" % e)
        except urllib2.URLError as e:
            print(e)
            sys.exit("Exit script with error code %s" % e)
        except urllib.error.URLError as e:
            print(e)
            sys.exit("Exit script with error code %s" % e)
        except urllib2.HTTPError as e:
            print(e)
            sys.exit("Exit script with error code %s" % e)

        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)
            sys.exit("Exit script with error code %s" % e)

    @staticmethod
    def _get_app_param_info(app_info, resultCount=1, resultKey='primaryGenreId'):
        """
        method to retrieve specific values from app_info dict using provided key.
        :param app_info: dict formatted app_info
        :param resultCount: to be used for instances of multiple result counts use case.
        :param resultKey: key for fetching value
        :return: returns value of specified key from app_info dictionary
        """
        try:
            assert app_info['results'][resultCount - 1][resultKey] is not None, "Null item"
            return app_info['results'][resultCount - 1][resultKey]
        except AssertionError as e:
            print("get_app_param_info", e)
            sys.exit("Exit script with error code %s" % e)
        except TypeError as e:
            print("get_app_param_info", e)
            sys.exit("Exit script with error code %s" % e)
        except:
            e = sys.exc_info()[0]
            print("Error: get_app_param_info %s" % e)
            sys.exit("Exit script with error code %s" % e)

    def _set_app_info_Primary(self):
        """
        setter method to set Primary app information.
        """
        self._Primary_app_info = self._fetch_app_info(self._Primary)

    def _get_app_info_Primary(self):
        """
        method to get Primary app information.
        :return: primary app information
        """
        return self._Primary_app_info

    def _set_app_info_Secondary(self):
        """
        setter method to set Secondary app information.
        """
        for items in self._Secondary:
            self._Secondary_app_info.append(self._fetch_app_info(items))

    def _set_app_info_Secondary_parallel(self):
        """
        setter method to set Secondary app information.
        Optimized for parallel processing of http requests.
        """

        results = Pool(4).map(self._fetch_app_info, self._Secondary, chunksize=5)
        for result in results:
            self._Secondary_app_info.append(result)

    def _get_app_info_Secondary(self):
        """
        method to get Secondary app information.
        :return: secondary app information
        """
        return self._Secondary_app_info

    def _get_similarity_score(self, dict1, dict2):
        """ method to compute and get similarity score.

        Similarity Criteria as defined:
        - Major score determiner1: primaryGenreId
            Criteria match contributes to 3 point scale(or 30% of total similarity score)
        - Major score determiner2: genreIds
            Match Criteria contributes to 2 point scale(or 20% of total similarity score)
            More Information:
                -if atleast 1 genreIds match, score 50% of criteria weight is set(1 point).
                -remaining 50% of criteria weight is determined by percentage of primary genreIds matches.
                    For example: Primary_app_info['genreIds':1001,1010,5001] and Secondary_app_info['genreIds':1001,1011]
                     will yield 33.3% match.
                     Assumptions:
                     - If all Primary_app_info[genreIds] can be a subset of Secondary_app_info[genreIds] to produce a
                     perfect match score for this sub-category.
        -Major score determiner3: trackName
         Match criteria contributes to 1 point scale (or 10% of total similarity score).
            More Information:
            Percentage match of string sequence of trackName is added to 10% of total similarity score.
            Assumptions:
            - Two applications with similar characteristics have higher similarity score if their trackName strings
            produce better percentage match results.
            For example, for Primary_app_info[trackName]=FlappyBird, Secondary_app_info[trackName]=AngryBird will produce
             a better string sequence match compared to Secondary_app_info[trackName]=FruitNinja.
        - Minor score determiner: 'isGameCenterEnabled', 'languageCodesISO2A', 'contentAdvisoryRating', 'artistId',
                                'formattedPrice'.
            Criteria contributes to 4 point scale or(40% of total similarity score).
            Assumptions:
             - All sub categories are given equal weight to impact the final Similarity score.
             - Apps with GameCenter enabled are assumed to get higher similarity score compared to apps with similar
             characteristics.
             - Apps with common languageCodes are assumed to get higher similarity score compared to apps with similar
             characteristics.
             - Apps with common contentAdvisoryRating are assumed to get higher similarity score compared to apps with
             similar characteristics.
             - Apps from same artistId are assumed to get higher similarity score compared to apps with similar
             characteristics.
             - Apps with common Price format are assumed to get higher similarity score compared to apps with similar
             characteristics.
        :param dict1: primary dictionary
        :param dict2: secondary dictionary
        :return: log string containing trackId,trackName, and similarity score
        """
        try:
            majorScoreDeterminer1 = ['primaryGenreId']
            majorScoreDeterminer2 = ['genreIds']
            Score = 0  # Base Score
            for items in majorScoreDeterminer2:

                for item1 in self._get_app_param_info(dict1, resultCount=1, resultKey=items):
                    if item1 in self._get_app_param_info(dict2, resultCount=1, resultKey=items):
                        if Score == 0:  # Add 50% base score for this category.
                            Score += 2 * .5
                        Score += 2 * .5 / len(self._get_app_param_info(dict1, resultCount=1, resultKey=items))

            for items in majorScoreDeterminer1:
                if str(self._get_app_param_info(dict1, resultCount=1, resultKey=items)) in str(
                        self._get_app_param_info(dict2, resultCount=1, resultKey=items)) and str(
                    self._get_app_param_info(dict2, resultCount=1, resultKey=items)) and str(
                    self._get_app_param_info(dict1, resultCount=1, resultKey=items)):
                    Score += (3 / len(majorScoreDeterminer1))

            nameMatchScore = difflib.SequenceMatcher(None,
                                                     self._get_app_param_info(dict1, resultCount=1,
                                                                              resultKey='trackName'),
                                                     self._get_app_param_info(dict2, resultCount=1,
                                                                              resultKey='trackName')).ratio()
            Score += nameMatchScore

            minorScoreDeterminer = ['isGameCenterEnabled', 'languageCodesISO2A', 'contentAdvisoryRating', 'artistId',
                                    'formattedPrice']

            for items in minorScoreDeterminer:
                if items == "formattedPrice":
                    if str(self._get_app_param_info(dict1, resultCount=1, resultKey=items)) == "Free" and str(
                            self._get_app_param_info(dict2, resultCount=1, resultKey=items)) == "Free":
                        Score += (4 / (len(minorScoreDeterminer)))
                    elif str(self._get_app_param_info(dict1, resultCount=1, resultKey=items)) == "Free" and str(
                            self._get_app_param_info(dict2, resultCount=1, resultKey=items)) != "Free":
                        continue
                    elif str(self._get_app_param_info(dict1, resultCount=1, resultKey=items)) != "Free" and str(
                            self._get_app_param_info(dict2, resultCount=1, resultKey=items)) == "Free":
                        continue
                    elif str(self._get_app_param_info(dict1, resultCount=1, resultKey=items)) != "Free" and str(
                            self._get_app_param_info(dict2, resultCount=1, resultKey=items)) != "Free":
                        Score += (4 / (len(minorScoreDeterminer)))
                else:
                    if str(self._get_app_param_info(dict1, resultCount=1, resultKey=items)) in str(
                            self._get_app_param_info(dict2, resultCount=1, resultKey=items)):
                        Score += (4 / (len(minorScoreDeterminer)))
            Score = round(Score, 1)
            log_str = "id" + str(self._get_app_param_info(dict2, resultCount=1, resultKey='trackId')) + " - " + str(
                self._get_app_param_info(dict2, resultCount=1, resultKey='trackName')) + "\tScore: " + str(Score)
        except AssertionError as e:
            print("Error: _get_similarity_score %s" % e)
            sys.exit("Exit script with error code %s" % e)
        except TypeError as e:
            print("Error: _get_similarity_score %s" % e)
            sys.exit("Exit script with error code %s" % e)
        except:
            e = sys.exc_info()[0]
            print("Error: _get_similarity_score %s" % e)
            sys.exit("Exit script with error code %s" % e)
        else:
            return log_str


def pretty_print_app_info(info_dict):
    """
    method to pretty print json data.
    :param info_dict: json data format
    """
    print(json.dumps(info_dict, sort_keys=True,
                     indent=4, separators=(',', ': ')))


def main(Primary, Secondary):
    """
    main method
    :param Primary: Primary app_id
    :param Secondary: list of secondary app_id
    """
    try:
        assert Primary, "Primary app_id is empty"
        assert len(Secondary), "Secondary list is empty"
        app_obj = AppInfo(Primary, Secondary)
        assert isinstance(app_obj, AppInfo), "Object Instance not created."

        app_obj._set_app_info_Primary()
        if sys.version_info < (3, 5):
            app_obj._set_app_info_Secondary()
        else:
            app_obj._set_app_info_Secondary_parallel()

        log_db = list()
        for items in app_obj._Secondary_app_info:
            log_db.append(app_obj._get_similarity_score(app_obj._get_app_info_Primary(), items))
        log_db.sort(key=lambda x: x.split()[-1], reverse=True)

        log_str = "PRIMARY: id" + str(
            app_obj._get_app_param_info(app_obj._get_app_info_Primary(), resultCount=1,
                                        resultKey='trackId')) + " - " + str(
            app_obj._get_app_param_info(app_obj._get_app_info_Primary(), resultCount=1, resultKey='trackName'))
        print(log_str)
        iter = 1
        for items in log_db:
            print(str(iter) + '. ' + items)
            iter += 1
    except AssertionError as e:
        print("Error: _main_ %s" % e)
        sys.exit("Exit script with error code %s" % e)
    except TypeError as e:
        print("Error: _main_", e)
        sys.exit("Exit script with error code %s" % e)
    except NameError as e:
        print("Error: _main_", e)
        sys.exit("Exit script with error code %s" % e)
    except:
        e = sys.exc_info()[0]
        print("Error: _main_ %s" % e)

if __name__ == "__main__":
    sys.exit(main())
