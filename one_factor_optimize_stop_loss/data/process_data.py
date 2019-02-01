# from MSSQL import MSSQL
import pandas as pd
import numpy as np
from scipy.stats import norm
import datetime
import re
# ms = MSSQL()
# new_con = ms.new_con

### raw_file1 should be qtv file, raw_file2 should be yahoo finance data
def process_data(raw_file1, raw_file2, out_file):
    df1 = pd.read_csv(raw_file1)
    df2 = pd.read_csv(raw_file2)
    df1.rename(columns={'trade_date': 'Date'}, inplace=True)
    df1 = df1[['Date', 'vp', 'q_g', 'tp_score']]
    df1['Date'] = df1['Date'].apply(lambda x: pd.to_datetime(x).strftime("%Y-%m-%d"))
    df2.dropna(how="any", inplace=True)
    df2.drop(df2[df2.values == 'null'].index, inplace=True)
    df2['openinterest'] = 0
    df_final = pd.merge(df2, df1, how='right', on='Date')
    df_final.set_index(['Date'], inplace=True)
    df_final = df_final.dropna()
    del df_final['Adj Close']
    df_final.index = pd.to_datetime(df_final.index)
    df_final.to_csv(out_file, date_format='%Y-%m-%d %H:%M:%S')


    # process data download from yahoo to the format that backtrader can recognize, file_name the name you want to input
    # out_file the output file, just change the date format to add hour minute and second.
class Meta_process(object):
    def process_data_from_Yahoo(self, file_name, out_file):
        df = pd.read_csv(file_name)
        df.dropna(how="any", inplace=True)
        df.drop(df[df.values == 'null'].index, inplace=True)
        try:
            df.set_index(['Date'], inplace=True)
            del df['Adj Close']
        except Exception:
            print (file_name + "didn't set Date index and delete Adj Close")
            pass
        df['openinterest'] = 0
        df.index = pd.to_datetime(df.index)
        df.to_csv(out_file, date_format='%Y-%m-%d %H:%M:%S')

    def read_the_existing_file(self, mypath):
        from os import listdir
        from os.path import isfile, join
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        return onlyfiles


### add tp data
class ProcessDataCalTP(Meta_process):
    def __init__(self, file_list):
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.file_list = file_list
        self.date_delta = 1250

    ### end_date default is today


    def _cal_mean(self, df):
        if len(df) < self.date_delta:
            mean = np.nanmean(df[0:, :], axis=0)
            for i in range(len(df) - 1):
                mean_temp = np.nanmean(df[i + 1:, :], axis=0)
                mean = np.vstack((mean, mean_temp))

        else:
            mean = np.nanmean(df[0:self.date_delta, :], axis=0)
            for i in range(self.date_delta - 1):
                mean_temp = np.nanmean(df[i + 1:i + 1 + self.date_delta, :], axis=0)
                mean = np.vstack((mean, mean_temp))
        return mean

    def _cal_std(self, df):
        if len(df) < self.date_delta:
            std = np.nanstd(df[0:, :], axis=0)
            for i in range(len(df) - 1):
                std_temp = np.nanstd(df[i + 1:, :], axis=0)
                std = np.vstack((std, std_temp))

        else:
            std = np.nanstd(df[0:self.date_delta, :], axis=0)
            for i in range(self.date_delta - 1):
                std_temp = np.nanstd(df[i + 1:i + 1 + self.date_delta, :], axis=0)
                std = np.vstack((std, std_temp))
        return std

    def _compare_date(self, df):
        if len(df) <= self.date_delta:
            df = df
        else:
            df = df[:self.date_delta]
        return df


    def _cal_tp(self, filepath):
        norm_func = np.vectorize(lambda x: norm.cdf(x))
        weight = np.array([0.5, 0.25, 0.25])
        # mean = np.array([0.08, 0.08, 0.08])
        df = pd.read_csv(filepath)
        if len(df) < 200:
            df['tp'] = np.nan
            return df
        else:
            df.sort_values(by='Date', ascending=False)
            df['ma_200d'] = df.rolling(window=200). mean()
            df['ma_100d'] = df.rolling(window=100). mean()
            df['ma_50d'] = df.rolling(window=50). mean()
            df = df[:-200]
            df = self._compare_date(df)

            ma_200d = np.array(df['ma_200d'])
            ma_100d = np.array(df['ma_100d'])
            ma_50d = np.array(df['ma_50d'])
            df = df['trade_Date'][:-1]
            df = self._compare_date(df)
            log_200d_slope = 250 * (np.log(ma_200d[:-1]) - np.log(ma_200d[1:]))
            log_100d_slope = 250 * (np.log(ma_100d[:-1]) - np.log(ma_100d[1:]))
            log_50d_slope = 250 * (np.log(ma_50d[:-1]) - np.log(ma_50d[1:]))
            matrix = np.column_stack([log_200d_slope, log_100d_slope, log_50d_slope])
            try:
                # mean = _cal_mean(matrix)
                std = self._cal_std(matrix)
            except Exception:
                raise ValueError("matrix calculation has an error")

            # matrix1 = _compare_date(matrix)
            deviation = (matrix - 0.08) / std
            norm_dist = norm_func(deviation)
            tp_score_temp = np.dot(norm_dist, weight).T * 100
            df['tp_score'] = tp_score_temp
            return df


    def main(self):
        for filepath in self.file_list:
            df = self._cal_tp(filepath)
            filepath_out = 'Yahoodata_after_modify_add_tp/' + filepath
            df.to_csv(filepath_out, date_format='%Y-%m-%d %H:%M:%S')


## reformat all the file in processed_data, auto-detect the file
def reformat_processed_data(filename = None):
    a = Meta_process()
    my_path = "D:\\backtrader\data\processed_data"
    list = a.read_the_existing_file(mypath=my_path)
    file_path_list = [(lambda x: my_path + '\\' + x)(x) for x in list]
    for path in file_path_list:
        a.process_data_from_Yahoo(path, path)


### read data from filename,and output the series for pyfolio
def get_symbol_returns(filename, start=None, end=None):
    try:
        px = pd.read_csv(filename)
    except Exception as e:
       raise ValueError('There is no file in the filepath you passed'.format(e), UserWarning)
    px['Date'] = pd.to_datetime(px['Date'])
    px.set_index('Date', drop=False, inplace=True)
    rets = px[['Close']].pct_change().dropna()
    rets.index = rets.index.tz_localize("UTC")
    try:
        rets = rets[(rets.index < start) & (rets.index > end)]
    except Exception:
        pass
        # raise ValueError('The start and end date you input is not right')
    stock_name = re.search('_data/(.*).csv', filename).group(1)
    rets.columns = [stock_name]
    rets = rets[stock_name]
    # try:
    #     rets = pd.Series(rets)
    # except Exception:
    #     raise TypeError('The dataframe you input can not be inverted into Series')
    return rets


if __name__ == '__main__':
    # reformat_processed_data()
    # process_data('C:\Users\wilsonZhang\Desktop\G_df.csv', 'raw_data\\0700.HK.csv', '700HK_qtv_final3.csv')
    # df = pd.read_csv("D:\\backtrader\data\processed_data\\0700.HK.csv")
    # df.dropna()
    # print df
    # rets = get_symbol_returns('D:/backtrader/data/processed_data/0700.HK.csv')
    process_data('factor_analysis/2353 TT EQUITY.csv', 'factor_analysis/2353.TW.csv', 'factor_analysis/2353 TT EQUITY processed.csv')
    # process_data('factor_analysis/285 HK EQUITY.csv', 'factor_analysis/0285.HK.csv', 'factor_analysis/285 HK EQUITY processed.csv')
    # process_data('factor_analysis/2353 TT EQUITY.csv', 'factor_analysis/2353.TW.csv', 'factor_analysis/2353 TT EQUITY processed.csv')
    # process_data('factor_analysis/700 HK EQUITY.csv', 'factor_analysis/0700.HK.csv', 'factor_analysis/700 HK EQUITY processed.csv')
    # process_data('factor_analysis/1211 HK EQUITY.csv', 'factor_analysis/1211.HK.csv', 'factor_analysis/1211 HK EQUITY processed.csv')
    # process_data('factor_analysis/1888 HK EQUITY.csv', 'factor_analysis/1888.HK.csv', 'factor_analysis/1888 HK EQUITY processed.csv')
    # process_data('factor_analysis/1212 HK EQUITY.csv', 'factor_analysis/1212.HK.csv', 'factor_analysis/1212 HK EQUITY processed.csv')
    # process_data('factor_analysis/ACES IJ EQUITY.csv', 'factor_analysis/ACES.JK.csv', 'factor_analysis/ACES IJ EQUITY processed.csv')
    # process_data('factor_analysis/SUNTV IN EQUITY.csv', 'factor_analysis/SUNTV.NS.csv', 'factor_analysis/SUNTV IN EQUITY processed.csv')
    # process_data('factor_analysis/GUJS IN EQUITY.csv', 'factor_analysis/GSPL.NS.csv', 'factor_analysis/GUJS IN EQUITY processed.csv')
    # process_data('factor_analysis/GUJS IN EQUITY.csv', 'factor_analysis/039130.KS.csv', 'factor_analysis/039130 KS EQUITY processed.csv')
    # a = Meta_process()
    # a.process_data_from_Yahoo(file_name= 'D:/backtrader/data/Yahoo_data/^HSI.csv', out_file ='D:/backtrader/data/processed_data/HSI.csv')


