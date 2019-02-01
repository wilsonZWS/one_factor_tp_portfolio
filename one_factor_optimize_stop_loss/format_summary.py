from matplotlib import pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from openpyxl import load_workbook
import seaborn as sns
import pickle


# df = pd.read_excel('C:\Users\wilsonZhang\Desktop\\research_result.xlsx', sheetname='avg_annual_return')


def format_dict_to_dataframe(groupby_list, pickle_name, columns):
    df = pd.DataFrame()
    objects1 = pd.read_pickle(pickle_name)
    # if if_avg_annual == True:
    #     columns = ['median_avg_annual_return', 'std_avg_annual_return',
    #                 'risk_adjusted_return', 'frequency', 'avg_period']
    #
    # else:
    #     columns = ['median_transaction_return', 'std_transaction_return',
    #                 'risk_adjusted_return', 'frequency', 'avg_period']

    for key in objects1[0].keys():
        summary_dict = objects1[0][key]
        index_list = range(len(summary_dict.apply(lambda x: x[0]).values))
        dict = {}
        m = len(groupby_list)
        for i in range(m):
            dict[groupby_list[i]] = summary_dict.apply(lambda x: x[i]).values
        for l in range(len(columns)):
            dict[columns[l]] = summary_dict.apply(lambda x: x[m + l]).values
        df_columns = groupby_list + columns

        summary_df = pd.DataFrame(data=dict, columns=df_columns, index=index_list)
        # summary_df = pd.DataFrame({'tp_xu':summary_dict.apply(lambda x: x[0]).values,
        #                            'tp_xd': summary_dict.apply(lambda x: x[1]).values,
        #                            'median_transaction_return': summary_dict.apply(lambda x: x[2]).values,
        #                            'std_transaction_return': summary_dict.apply(lambda x: x[3]).values,
        #                            'risk_adjusted_return': summary_dict.apply(lambda x: x[4]).values,
        #                            'frequency': summary_dict.apply(lambda x: x[5]).values,
        #                            'avg_period': summary_dict.apply(lambda x: x[6]).values},
        #                             columns= columns, index=range(len(summary_dict)))
        summary_df['frequency_pct'] = summary_df['frequency']/ summary_df['frequency'].sum()
        summary_df['blp_ticker'] = key
        df = df.append(summary_df)
    return df


def format_raw_research_main(group_list, summary_list, in_file='factor_analysis/One_factor_rolling_stoploss.xlsx', pkl_file='rolling_stoploss_research.pkl',
                             path='factor_analysis/rolling_stoploss_research.xlsx', if_pickle_exist=True, if_avg_annual=True):

    if if_avg_annual == True:
        col = ['avg_annual_return', 'std_annual_return',
                    'risk_adjusted_return', 'frequency', 'avg_period']
    else:
        col = ['avg_transaction_return', 'std_transaction_return', 'risk_adjusted_return',
               'frequency', 'avg_period']
    # col = ['std_transaction_return', 'risk_adjusted_return', 'frequency', 'avg_period']
    df = format_dict_to_dataframe(group_list, pickle_name=pkl_file, columns=col)
    return df



def raw_data_summary_trans_return():
    def delete_outlier_format_summary(df, col):
        # four = pd.Series(df[col]).describe()
        # Q1 = four['25%']
        # Q3 = four['75%']
        # IQR = Q3 - Q1
        # upper = Q3 + 2 * IQR
        # lower = Q1 - 2 * IQR
        # df = df[(df[col] <= upper) & (df[col] >= lower)]
        avg = np.nanmean(df[col])
        std = np.nanstd(df[col])
        risk_adjusted_return = avg/std
        # avg_fre = np.nanmean(df['frequency'])
        # avg_period = np.nanmean(df['avg_period'])
        return [avg, std, risk_adjusted_return]
    # df = pd.read_excel('C:\Users\wilsonZhang\Desktop\\research_result.xlsx', sheetname='avg_annual_return')
    df = pd.read_excel('count_close_type_all.xlsx', sheetname='Sheet1')
    # df['tp_xu'] = df['tp_xu'].fillna(method='ffill')
    # df['tp_windowing'] = df['tp_windowing'].fillna(method='ffill')
    # df[(df['median_avg_annual_return'] == np.inf)]
    # df.pivot(index='tp_xu', columns='tp_windowing', values='median_avg_annual_return')

    gdf1 = df.groupby(['tp_xu', 'tp_windowing', 'stoploss']).apply(lambda x: delete_outlier_format_summary(x, col='trans_return'))
    # gdf1 = df.groupby(['tp_xu', 'tp_windowing'])['avg_annual_return'].agg(['mean'])
    # gdf2 = df.groupby(['tp_xu', 'tp_windowing'])['risk_adjusted_return'].agg(['mean'])

    gdf1 = pd.DataFrame({'avg': gdf1.apply(lambda x: x[0]).values,
                         'std': gdf1.apply(lambda x: x[1]).values,
                         'risk_adjusted_return': gdf1.apply(lambda x: x[2]).values
                         }, index=gdf1.index)

    # writer = pd.ExcelWriter("mean_summary.xlsx", engine='openpyxl')
    gdf1.to_excel("mean_summary_trans_return.xlsx", sheet_name='mean_summary_trans_return')
    # gdf2.to_excel(writer, sheet_name='risk_adjusted_return')



def raw_data_summary_avg_return():
    def delete_outlier_format_summary(df, col):
        four = pd.Series(df[col]).describe()
        Q1 = four['25%']
        Q3 = four['75%']
        IQR = Q3 - Q1
        upper = Q3 + 1.8 * IQR
        lower = Q1 - 1.8 * IQR
        df = df[(df[col] <= upper) & (df[col] >= lower)]
        avg = np.nanmean(df[col])
        std = np.nanstd(df[col])
        risk_adjusted_return = avg/std
        avg_fre = np.nanmean(df['frequency'])
        avg_period = np.nanmean(df['avg_period'])
        return [avg, std, risk_adjusted_return, avg_fre, avg_period]
    # df = pd.read_excel('C:\Users\wilsonZhang\Desktop\\research_result.xlsx', sheetname='avg_annual_return')
    df = pd.read_excel('C:\Users\wilsonZhang\Desktop\\research_result.xlsx', sheetname='raw_data')
    df['tp_xu'] = df['tp_xu'].fillna(method='ffill')
    df['tp_windowing'] = df['tp_windowing'].fillna(method='ffill')
    # df[(df['median_avg_annual_return'] == np.inf)]
    # df.pivot(index='tp_xu', columns='tp_windowing', values='median_avg_annual_return')

    gdf1 = df.groupby(['tp_xu', 'tp_windowing', 'stoploss']).apply(lambda x: delete_outlier_format_summary(x, col='avg_annual_return'))
    # gdf1 = df.groupby(['tp_xu', 'tp_windowing'])['avg_annual_return'].agg(['mean'])
    # gdf2 = df.groupby(['tp_xu', 'tp_windowing'])['risk_adjusted_return'].agg(['mean'])

    gdf1 = pd.DataFrame({'avg': gdf1.apply(lambda x: x[0]).values,
                         'std': gdf1.apply(lambda x: x[1]).values,
                         'risk_adjusted_return': gdf1.apply(lambda x: x[2]).values,
                         'avg_fre':gdf1.apply(lambda x: x[3]).values,
                         'avg_period': gdf1.apply(lambda x: x[4]).values
                         }, index=gdf1.index)

    # writer = pd.ExcelWriter("mean_summary.xlsx", engine='openpyxl')
    gdf1.to_excel("mean_summary2.xlsx", sheet_name='mean_annual_return')
    # gdf2.to_excel(writer, sheet_name='risk_adjusted_return')


def summary_close_type(file = "count_close_type_all.xlsx", out_file="close_type_stop_loss_pivot_table.xlsx",
                       group_list =['stoploss', 'close_type'], col='annual_return'):
    def delete_outlier_format_summary(df, col):
        four = pd.Series(df[col]).describe()
        Q1 = four['25%']
        Q3 = four['75%']
        IQR = Q3 - Q1
        upper = Q3 + 1.8 * IQR
        lower = Q1 - 1.8 * IQR
        df = df[(df[col] <= upper) & (df[col] >= lower)]
        avg = np.nanmean(df[col])
        std = np.nanstd(df[col])
        risk_adjusted_return = avg/std
        return [avg, std, risk_adjusted_return]
    # df = pd.read_excel('C:\Users\wilsonZhang\Desktop\\research_result.xlsx', sheetname='avg_annual_return')
    df = pd.read_excel(file, sheetname='Sheet1')
    # df[(df['median_avg_annual_return'] == np.inf)]
    # df.pivot(index='tp_xu', columns='tp_windowing', values='median_avg_annual_return')

    gdf1 = df.groupby(group_list).apply(lambda x: delete_outlier_format_summary(x, col=col))
    # gdf1 = df.groupby(['tp_xu', 'tp_windowing'])['avg_annual_return'].agg(['mean'])
    # gdf2 = df.groupby(['tp_xu', 'tp_windowing'])['risk_adjusted_return'].agg(['mean'])

    gdf1 = pd.DataFrame({'avg': gdf1.apply(lambda x: x[0]).values,
                         'std': gdf1.apply(lambda x: x[1]).values,
                         'risk_adjusted_return': gdf1.apply(lambda x: x[2]).values
                         }, index=gdf1.index)
    gdf1.reset_index(level=group_list, inplace=True)

    # writer = pd.ExcelWriter("mean_summary.xlsx", engine='openpyxl')
    gdf1.to_excel(out_file, sheet_name='summary')




def summary_close_type_60_10(file = "count_close_type_all.xlsx"):
    def delete_outlier_format_summary(df, col):
        four = pd.Series(df[col]).describe()
        Q1 = four['25%']
        Q3 = four['75%']
        IQR = Q3 - Q1
        upper = Q3 + 1.8 * IQR
        lower = Q1 - 1.8 * IQR
        df = df[(df[col] <= upper) & (df[col] >= lower)]
        avg = np.nanmean(df[col])
        std = np.nanstd(df[col])
        risk_adjusted_return = avg/std
        return [avg, std, risk_adjusted_return]
    # df = pd.read_excel('C:\Users\wilsonZhang\Desktop\\research_result.xlsx', sheetname='avg_annual_return')
    df = pd.read_excel(file, sheetname='Sheet1')
    # df[(df['median_avg_annual_return'] == np.inf)]
    # df.pivot(index='tp_xu', columns='tp_windowing', values='median_avg_annual_return')
    df = df[(df['tp_xu'] == 60) & (df['tp_windowing'] == 10)]
    gdf1 = df.groupby(['stoploss', 'close_type']).apply(lambda x: delete_outlier_format_summary(x, col='annual_return'))
    # gdf1 = df.groupby(['tp_xu', 'tp_windowing'])['avg_annual_return'].agg(['mean'])
    # gdf2 = df.groupby(['tp_xu', 'tp_windowing'])['risk_adjusted_return'].agg(['mean'])

    gdf1 = pd.DataFrame({'avg': gdf1.apply(lambda x: x[0]).values,
                         'std': gdf1.apply(lambda x: x[1]).values,
                         'risk_adjusted_return': gdf1.apply(lambda x: x[2]).values
                         }, index=gdf1.index)

    # writer = pd.ExcelWriter("mean_summary.xlsx", engine='openpyxl')
    gdf1.to_excel("close_type_stop_loss_pivot_table60_10.xlsx", sheet_name='summary')

if __name__ == '__main__':
    # df = format_raw_research_main(group_list=['tp_xu', 'tp_windowing', 'stoploss'],
    #                          summary_list=['tp_xu', 'tp_windowing'],
    #                          in_file='data_summary.xlsx',
    #                          if_pickle_exist=True, if_avg_annual=True,
    #                          path='research_result.xlsx',
    #                          pkl_file='summary_result.pkl')
    summary_close_type(file='count_close_type_all0.6~1.0.xlsx', out_file="close_type_stop_loss_pivot_table_trans_return0.6~1.0.xlsx",
                       group_list=['tp_xu', 'tp_windowing', 'stoploss'], col='trans_return')
    # raw_data_summary_trans_return()
    # summary_close_type_60_10()



