from matplotlib import pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from openpyxl import load_workbook
import seaborn as sns

def delete_outlier_format_summary(df, col):
    four = pd.Series(df[col]).describe()
    Q1 = four['25%']
    Q3 = four['75%']
    IQR = Q3 - Q1
    upper = Q3 + 1.5 * IQR
    lower = Q1 - 1.5 * IQR
    tp_xu = df['tp_xu'].iloc[0]
    tp_xd = df['tp_xd'].iloc[0]
    df = df[(df[col] <= upper) & (df[col] >= lower)]
    avg = np.nanmean(df[col])
    std = np.nanstd(df[col])
    risk_adjusted_return = avg/std
    frequency = len(df)
    avg_period = np.nanmean(df['period'])
    return [tp_xu, tp_xd, avg, std, risk_adjusted_return, frequency, avg_period]


def format_cluster_excel(ticker):
    # fig = plt.figure()
    df = pd.read_excel('One_factor_tp_portfolio.xlsx', sheetname=ticker, usecols=range(20, 39))
    df.index = range(len(df))
    df.rename(columns={'tp_xd.1': 'tp_xd',
                       'tp_xu.1': 'tp_xu'}, inplace=True)
    df.dropna(how='any', inplace=True)
    df['tp_xu'].replace([70, 80, 90], '70~90', inplace=True)
    df['tp_xu'].replace([40, 50, 60], '40~60', inplace=True)
    df['tp_xu'].replace([10, 20, 30], '10~30', inplace=True)
    df['tp_xd'].replace([70, 80, 90], '70~90', inplace=True)
    df['tp_xd'].replace([40, 50, 60], '40~60', inplace=True)
    df['tp_xd'].replace([10, 20, 30], '10~30', inplace=True)
    grouped = df.groupby(['tp_xu', 'tp_xd'])
    summary_dict = grouped.apply(lambda x: delete_outlier_format_summary(x, col='annual_return'), )
    summary_df = pd.DataFrame({'tp_xu':summary_dict.apply(lambda x: x[0]).values,
                               'tp_xd': summary_dict.apply(lambda x: x[1]).values,
                               'avg_annual_return': summary_dict.apply(lambda x: x[2]).values,
                               'std_annual_return': summary_dict.apply(lambda x: x[3]).values,
                               'annual_risk_adjusted_return': summary_dict.apply(lambda x: x[4]).values,
                               'frequency': summary_dict.apply(lambda x: x[5]).values,
                               'avg_period': summary_dict.apply(lambda x: x[6]).values},
                                columns=['tp_xu', 'tp_xd', 'avg_annual_return', 'std_annual_return',
                                         'annual_risk_adjusted_return', 'frequency', 'avg_period'], index=range(len(summary_dict)))
    summary_df['frequency_pct'] = summary_df['frequency']/ summary_df['frequency'].sum()
    path = 'tp_portfolio_for_heatmap_summary.xlsx'
    try:
        book1 = load_workbook(path)
    except Exception:
        df_empty = pd.DataFrame()
        df_empty.to_excel(path)
    writer = pd.ExcelWriter(path, engine='openpyxl')
    writer.book = book1
    summary_df.to_excel(writer, sheet_name=ticker)
    writer.save()
    writer.close()


    # # df = df[abs(df['risk_adjusted_return']) < 8]
    # X = np.array(summary_df['tp_xd'].values)
    # Y = np.array(summary_df['tp_xu'].values)
    # Z = np.array(summary_df[col].values)
    # ax = fig.add_subplot(1, 1, 1, projection='3d')
    # p = ax.plot_trisurf(X, Y, Z, cmap='viridis')
    # ax.legend()
    # ax.set_title(ticker)
    # ax.set_xlim(1, 3)
    # ax.set_ylim(1, 3)
    # # ax.set_zlim(0, 30)
    # ax.set_xlabel('Sell:tp_xd_cluster')
    # ax.set_ylabel('Buy:tp_xu_cluster')
    # ax.set_zlabel(col)
    # fig.colorbar(p)
    # plt.show()
    # path = "C:\Users\wilsonZhang\Desktop\\backtest_chart\\clusterd_chart\\" + ticker + "_" + col + ".png"
    # fig.savefig(path)


def draw_heatmap(ticker, col):
    df = pd.read_excel('tp_portfolio_for_heatmap_summary.xlsx', sheetname=ticker, usecols=range(8))
    df.index = range(len(df))
    df[['avg_annual_return', 'std_annual_return', 'frequency_pct']]=\
        df[['avg_annual_return', 'std_annual_return', 'frequency_pct']].round(4)
    df['avg_period'] = df['avg_period'].apply(lambda x: int(x))
    # df['frequency_pct'] = pd.Series(["{0:.2f}%".format(val * 100) for val in df['frequency_pct']], index=df.index)
    # data = sns.load_dataset(df)
    data1 = df.pivot("tp_xu", "tp_xd", col)
    if col == 'avg_period':
        ax = sns.heatmap(data1, annot=True, fmt='d')
    else:
        ax = sns.heatmap(data1, annot=True)
    if col == 'frequency':
        total_time = np.sum(df['frequency'])
        ax.set_title(ticker + " " + col + ' total_time:' + str(total_time))
    else:
        ax.set_title(ticker + " " + col)
    path = "heat_map_chart/" + ticker + "_" + col + ".png"
    # fig = ax.get_figure()
    plt.savefig(path)
    plt.close()



def main():
    x1 = pd.ExcelFile('One_factor_tp_portfolio.xlsx')
    sheet_name_list = x1.sheet_names
    ticker_list = sheet_name_list[1:]
    count = 0
    # for ticker in ticker_list:
    #     format_cluster_excel(ticker)
    #     count = count + 1
    #     print count

    for ticker in ticker_list:
        draw_heatmap(ticker, col='avg_annual_return')
        draw_heatmap(ticker, col='std_annual_return')
        draw_heatmap(ticker, col='annual_risk_adjusted_return')
        draw_heatmap(ticker, col='frequency')
        draw_heatmap(ticker, col='avg_period')
        draw_heatmap(ticker, col='frequency_pct')
        count = count + 1
        print count

if __name__ == '__main__':
    main()


