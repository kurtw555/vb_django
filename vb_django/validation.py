

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
