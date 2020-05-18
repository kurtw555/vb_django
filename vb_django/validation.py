

class Validator:

    @staticmethod
    def validate_point(latitude, longitude):
        """
        Validate a given latitude, longitude point
        :param latitude: Latitude value, valid between -90.0 and 90
        :param longitude: Longitude value, valide between -180.0 and 180.0
        :return: bool, True if both latitude and longitude are valid, otherwise False
        """
        valid = False
        if isinstance(latitude, float) and isinstance(longitude, float):
            if -90.0 < latitude < 90.0 and -180.0 < longitude < 180.0:
                valid = True
        return valid

    @staticmethod
    def validate_inputlist(required_list, actual_list):
        """
        Compares the two lists and will compile a message stating which, if any,
        of the elements are missing from the actual list.
        :param required_list: A list of required elements that the actual list is compared to.
        :param actual_list: A list of elements compared to the required list (keys of a POST request)
        :return: A blank string if all elements in actual are in required, otherwise a string stating which are missing.
        """
        result = ""
        missing = []
        for r in required_list:
            if r not in actual_list:
                missing.append(r)
        if len(missing) > 0:
            result = "The following required parameters were not found: {}".format(",".join(missing))
        return result
