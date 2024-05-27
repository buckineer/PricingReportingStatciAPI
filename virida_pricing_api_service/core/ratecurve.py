import numpy as np
import datetime as dt


def convert_tenors(tenors):
    # convert tenors to years
    new_tenors = np.repeat(np.NaN, len(tenors))
    for i, o in enumerate(tenors):
        if o[-1] == 'M':
            new_tenors[i] = int(o[:-1]) / 12.
        elif o[-1] == 'D':
            new_tenors[i] = int(o[:-1]) / 365.
        else:
            new_tenors[i] = int(o[:-1])
    return new_tenors


class RatesCurve:
    def __init__(self, *args, **kwargs):
        if 'valuation_date' not in kwargs:
            raise Exception('Missing valuation_date parameter')
        if 'currency' not in kwargs:
            raise Exception('Missing currency parameter')

        self.valuation_date = kwargs.get('valuation_date')
        self.currency = kwargs.get('currency')

        if ('tenor' in kwargs) and ('rate' in kwargs):
            if not isinstance(kwargs.get('tenor'), list):
                raise Exception('Incorrect parameter. tenor should be an array')
            if not isinstance(kwargs.get('rate'), list):
                raise Exception('Incorrect parameter. rate should be an array')

            _tenors = kwargs.get('tenor')
            _rate = kwargs.get('rate')
            _time = convert_tenors(_tenors)
            _time_sorted = sorted(_time)
            _rate_sorted = [x for _, x in sorted(zip(_time, _rate))]

        elif ('time' in kwargs) and ('rate' in kwargs):
            if not isinstance(kwargs.get('time'), list):
                raise Exception('Incorrect parameter. time should be an array')
            if not isinstance(kwargs.get('rate'), list):
                raise Exception('Incorrect parameter. rate should be an array')
            if len(kwargs.get('time')) != len(kwargs.get('rate')):
                raise Exception('Incorrect parameters. Array time and rate must be of same size')

            _time = kwargs.get('time')
            _rate = kwargs.get('rate')
            _time_sorted = sorted(_time)
            _rate_sorted = [x for _, x in sorted(zip(_time, _rate))]
            # print(_time_sorted, _rate_sorted)

        # common code
        self.abscissas = _time_sorted
        self.ordinates = _rate_sorted
        self.interpolation_space = 'rate'

    def get_rate(self, date):
        if self.interpolation_space == 'rate':
            if date < self.valuation_date:
                raise Exception("Error. Date requested is before valuation_date")

            t = (date - self.valuation_date).days / 365.
            return np.interp(t, self.abscissas, self.ordinates)
        else:
            raise Exception("Undefined interpolation space")


if __name__ == "__main__":

    my_curve = RatesCurve(valuation_date=dt.datetime.now(), currency='USD', tenor=["6M", "3M", "2Y"],
                          rate=[0.015, 0.01, 0.03])

    # my_curve = RatesCurve(valuation_date=dt.datetime.now(), currency='USD', time=[6./12., 3./12., 2.],
    #                      rate=[0.015, 0.01, 0.03])

    print(convert_tenors(["10D", "3M", "6M", "2Y"]))

    date_arr = [dt.datetime(2021, 3, 6), dt.datetime(2021, 6, 3), dt.datetime(2022, 5, 3)]

    for d in date_arr:
        print('{0}: {1}'.format(d.strftime('%Y-%m-%d'), my_curve.get_rate(d)))
