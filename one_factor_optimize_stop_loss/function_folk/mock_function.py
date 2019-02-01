from collections import OrderedDict
import empyrical as ep
import numpy as np
from pyfolio import timeseries
from pyfolio.utils import (APPROX_BDAYS_PER_MONTH)
import backtrader as bt
# import matplotlib.pyplot as plt
import pandas as pd
from one_factor_optimize_stop_loss.data.process_data import get_symbol_returns
# import backtrader.plot as btp


STAT_FUNCS_PCT = [
    'Annual return',
    'Cumulative returns',
    'Annual volatility',
    'Max drawdown',
    'Daily value at risk',
    'Daily turnover'
]
## rewrite the plot function, add save figure function


################# get the performance matrix
# @patch('pyfolio.plotting.show_perf_stats')
def show_perf_stats_beta(returns, factor_returns=None, positions=None,
                        transactions=None, turnover_denom='AGB',
                        live_start_date=None, bootstrap=False,
                        header_rows=None):
    """
    Prints some performance metrics of the strategy.
    - Shows amount of time the strategy has been run in backtest and
      out-of-sample (in live trading).
    - Shows Omega ratio, max drawdown, Calmar ratio, annual return,
      stability, Sharpe ratio, annual volatility, alpha, and beta.
    Parameters
    ----------
    returns : pd.Series
        Daily returns of the strategy, noncumulative.
         - See full explanation in tears.create_full_tear_sheet.
    factor_returns : pd.Series, optional
        Daily noncumulative returns of the benchmark factor to which betas are
        computed. Usually a benchmark such as market returns.
         - This is in the same style as returns.
    positions : pd.DataFrame, optional
        Daily net position values.
         - See full explanation in create_full_tear_sheet.
    transactions : pd.DataFrame, optional
        Prices and amounts of executed trades. One row per trade.
        - See full explanation in tears.create_full_tear_sheet
    turnover_denom : str, optional
        Either AGB or portfolio_value, default AGB.
        - See full explanation in txn.get_turnover.
    live_start_date : datetime, optional
        The point in time when the strategy began live trading, after
        its backtest period.
    bootstrap : boolean, optional
        Whether to perform bootstrap analysis for the performance
        metrics.
         - For more information, see timeseries.perf_stats_bootstrap
    header_rows : dict or OrderedDict, optional
        Extra rows to display at the top of the displayed table.
    """

    if bootstrap:
        perf_func = timeseries.perf_stats_bootstrap
    else:
        perf_func = timeseries.perf_stats

    perf_stats_all = perf_func(
        returns,
        factor_returns=factor_returns,
        positions=positions,
        transactions=transactions,
        turnover_denom=turnover_denom)

    date_rows = OrderedDict()
    if len(returns.index) > 0:
        date_rows['Start date'] = returns.index[0].strftime('%Y-%m-%d')
        date_rows['End date'] = returns.index[-1].strftime('%Y-%m-%d')

    if live_start_date is not None:
        live_start_date = ep.utils.get_utc_timestamp(live_start_date)
        returns_is = returns[returns.index < live_start_date]
        returns_oos = returns[returns.index >= live_start_date]

        positions_is = None
        positions_oos = None
        transactions_is = None
        transactions_oos = None

        if positions is not None:
            positions_is = positions[positions.index < live_start_date]
            positions_oos = positions[positions.index >= live_start_date]
            if transactions is not None:
                transactions_is = transactions[(transactions.index <
                                                live_start_date)]
                transactions_oos = transactions[(transactions.index >
                                                 live_start_date)]

        perf_stats_is = perf_func(
            returns_is,
            factor_returns=factor_returns,
            positions=positions_is,
            transactions=transactions_is,
            turnover_denom=turnover_denom)

        perf_stats_oos = perf_func(
            returns_oos,
            factor_returns=factor_returns,
            positions=positions_oos,
            transactions=transactions_oos,
            turnover_denom=turnover_denom)
        if len(returns.index) > 0:
            date_rows['In-sample months'] = int(len(returns_is) /
                                                APPROX_BDAYS_PER_MONTH)
            date_rows['Out-of-sample months'] = int(len(returns_oos) /
                                                    APPROX_BDAYS_PER_MONTH)

        perf_stats = pd.concat(OrderedDict([
            ('In-sample', perf_stats_is),
            ('Out-of-sample', perf_stats_oos),
            ('All', perf_stats_all),
        ]), axis=1)
    else:
        if len(returns.index) > 0:
            date_rows['Total months'] = int(len(returns) /
                                            APPROX_BDAYS_PER_MONTH)
        perf_stats = pd.DataFrame(perf_stats_all, columns=['Backtest'])

    for column in perf_stats.columns:
        for stat, value in perf_stats[column].iteritems():
            if stat in STAT_FUNCS_PCT:
                perf_stats.loc[stat, column] = str(np.round(value * 100,
                                                            1)) + '%'
    if header_rows is None:
        header_rows = date_rows
    else:
        header_rows = OrderedDict(header_rows)
        header_rows.update(date_rows)

    return perf_stats
    # utils.print_table(
    #     perf_stats,
    #     float_format='{0:.2f}'.format,
    #     header_rows=header_rows,
    # )


class PerformanceReport():
    """ Report with performce stats for given backtest run
    """
    def __init__(self, stratbt, Indexinfilename, outfilename, commission=None):
        self.stratbt = stratbt  # works for only 1 stategy
        self.Indexinfilename = Indexinfilename
        self.outfilename = outfilename
        self.commission = commission

    def get_startcash(self):
        return self.stratbt.broker.startingcash


    def get_stats(self):
        st = self.stratbt
        pyfoliozer = st.analyzers.getbyname('pyfolio')
        returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
        dt = returns.index
        trade_analysis = st.analyzers.myTradeAnalysis.get_analysis()
        rpl = trade_analysis.pnl.net.total
        total_return = rpl / self.get_startcash()
        total_number_trades = trade_analysis.total.total
        trades_closed = trade_analysis.total.closed
        bt_period = dt[-1] - dt[0]
        bt_period_days = bt_period.days
        kpi = {# PnL
               'start_cash': self.get_startcash(),
               'rpl': rpl,
               'result_won_trades': trade_analysis.won.pnl.total,
               'result_lost_trades': trade_analysis.lost.pnl.total,
               'profit_factor': (-1 * trade_analysis.won.pnl.total / trade_analysis.lost.pnl.total),
               'rpl_per_trade': rpl / trades_closed,
               'total_return': 100 * total_return,
               'annual_return': (100 * (1 + total_return)**(365.25 / bt_period_days) - 100),
               # trades
               'total_number_trades': total_number_trades,
               'trades_closed': trades_closed,
               'pct_winning': 100 * trade_analysis.won.total / trades_closed,
               'pct_losing': 100 * trade_analysis.lost.total / trades_closed,
               'avg_money_winning': trade_analysis.won.pnl.average,
               'avg_money_losing':  trade_analysis.lost.pnl.average,
               'best_winning_trade': trade_analysis.won.pnl.max,
               'worst_losing_trade': trade_analysis.lost.pnl.max,
               }
        return kpi

    def generate_excel_report(self, template = None):
        st = self.stratbt
        pyfoliozer = st.analyzers.getbyname('pyfolio')
        returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
        ### need to first calculate stats_dict1 becauce return index datetime should be include hour minute and seconds.
        benchmark_rets = get_symbol_returns(filename=self.Indexinfilename)
        stats_dict1 = show_perf_stats_beta(returns, benchmark_rets,
                                          positions=positions,
                                          transactions=transactions)
        stats_dict = self.get_stats()
        stats_dict = pd.DataFrame.from_dict(stats_dict, orient='index')
        stats_dict.rename(columns={0: 'Backtest'}, inplace=True)
        stats_dict = stats_dict.append(stats_dict1)
        stats_dict = stats_dict.round(2)

        # format position
        positions.index.names = ['date']
        positions.index = positions.index.strftime('%Y-%m-%d')
        positions = positions.round(2)

        # format returns
        returns = pd.DataFrame(returns)
        returns.index = returns.index.strftime('%Y-%m-%d')
        returns = returns.round(2)

        ## format transactions df
        transactions.index = transactions.index.strftime('%Y-%m-%d')
        transactions = transactions.round({'price': 2})

        ### get stats_dict run out by pyfolio
        # stats_dict = pd.DataFrame(stats_dict)
        # stats_dict.update(stats_dict1)
        if template== None:
        ### default template
            writer = pd.ExcelWriter(self.outfilename)
            positions.to_excel(writer, sheet_name="backtest_report")
            transactions.to_excel(writer, sheet_name="backtest_report", startcol=5)
            returns.to_excel(writer, sheet_name="backtest_report", startcol=13)
            stats_dict.to_excel(writer, sheet_name="backtest_report", startcol=16)
            writer.save()

        else:
        ### first template
            writer = pd.ExcelWriter(self.outfilename)
            positions.to_excel(writer, sheet_name="trade_positions")
            transactions.to_excel(writer, sheet_name="transactions")
            returns.to_excel(writer, sheet_name="returns")
            stats_dict.to_excel(writer, sheet_name="trade_parameter")
            writer.save()


#### this is just for tp backtest
class PerformanceReport2(PerformanceReport):
    def generate_excel_report(self, commission, template=None):
        st = self.stratbt
        pyfoliozer = st.analyzers.getbyname('pyfolio')
        returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
        ### need to first calculate stats_dict1 becauce return index datetime should be include hour minute and seconds.
        benchmark_rets = get_symbol_returns(filename=self.Indexinfilename)
        stats_dict1 = show_perf_stats_beta(returns, benchmark_rets,
                                          positions=positions,
                                          transactions=transactions)
        stats_dict = self.get_stats()
        stats_dict = pd.DataFrame.from_dict(stats_dict, orient='index')
        stats_dict.rename(columns={0: 'Backtest'}, inplace=True)
        stats_dict = stats_dict.append(stats_dict1)
        stats_dict = stats_dict.round(2)

        # format position
        positions.index.names = ['date']
        positions.index = positions.index.strftime('%Y-%m-%d')
        positions = positions.round(2)

        # format returns
        returns = pd.DataFrame(returns)
        returns.index = returns.index.strftime('%Y-%m-%d')
        returns = returns.round(2)

        ## format transactions df
        transactions.index = transactions.index.strftime('%Y-%m-%d')
        transactions = transactions.round({'price': 2})
        transactions['commission'] = abs(transactions['value'] * commission)
        transactions['action'] = transactions['amount'].apply(lambda x: 'Buy' if x > 0 else 'Sell')
        # transactions['cost'] = transactions.apply(lambda row: '' if row.value < 0 else)

        # transactions['net'] =
        # transactions['gross']
        # transactions['net']

        ### get stats_dict run out by pyfolio
        # stats_dict = pd.DataFrame(stats_dict)
        # stats_dict.update(stats_dict1)
        if template== None:
        ### default template
            writer = pd.ExcelWriter(self.outfilename)
            positions.to_excel(writer, sheet_name="backtest_report")
            transactions.to_excel(writer, sheet_name="backtest_report", startcol=5)
            returns.to_excel(writer, sheet_name="backtest_report", startcol=13)
            stats_dict.to_excel(writer, sheet_name="backtest_report", startcol=16)
            writer.save()
        else:
        ### first template
            writer = pd.ExcelWriter(self.outfilename)
            positions.to_excel(writer, sheet_name="trade_positions")
            transactions.to_excel(writer, sheet_name="transactions")
            returns.to_excel(writer, sheet_name="returns")
            stats_dict.to_excel(writer, sheet_name="trade_parameter")
            writer.save()


# writer.save()
class Cerebro(bt.Cerebro):
    def __init__(self, **kwds):
        super(Cerebro, self).__init__(**kwds)
        self.add_report_analyzers()


    def add_report_analyzers(self):
        """ Adds performance stats, required for report
        """
        self.addanalyzer(bt.analyzers.PyFolio)
        self.addanalyzer(bt.analyzers.DrawDown,
                         _name="myDrawDown")
        self.addanalyzer(bt.analyzers.AnnualReturn,
                         _name="myReturn")
        self.addanalyzer(bt.analyzers.TradeAnalyzer,
                         _name="myTradeAnalysis")

### runstrates is the result that will create after cerebro.run
    def get_strategy_backtest(self):
        return self.runstrats[0][0]


    ## the result input here should be the things run out by cerebro.run()
    def report(self, outfilename, infilename=None, commission=None):
        bt = self.get_strategy_backtest()
        rpt =PerformanceReport(bt, Indexinfilename=infilename, outfilename=outfilename, commission=commission)
        rpt.generate_excel_report()


    # def processPlots(self, cerebro, numfigs=1, iplot=True, start=None, end=None, width=16, height=9, dpi=300, tight=True, use=None, **kwargs):
    #     # if self._exactbars > 0:
    #     #     return
    #     from backtrader import plot
    #     if cerebro.p.oldsync:
    #         plotter = plot.Plot_OldSync(**kwargs)
    #     else:
    #         plotter = plot.Plot(**kwargs)
    #
    #     figs = []
    #     for stratlist in cerebro.runstrats:
    #         for si, strat in enumerate(stratlist):
    #             rfig = plotter.plot(strat, figid=si * 100,
    #                                 numfigs=numfigs, iplot=iplot,
    #                                 start=start, end=end, use=use)
    #             figs.append(rfig)
    #             # this blocks code execution
    #             # plotter.show()
    #     for fig in figs:
    #         for f in fig:
    #             f.savefig('chart/backtest_fig.png', bbox_inches='tight')
    #     return figs


# class Plotter(btp.Plot):
#     def __init__(self):
#         super(Plotter, self).__init__(volup='#60cc73')  # custom color for volume up bars
#
#     def show(self):
#         mng = self.mpyplot.get_current_fig_manager()
#         mng.window.state('zoomed')
#         self.mpyplot.savefig('chart/backtest_fig.png', bbox_inches='tight', dpi=400)
#         self.mpyplot.show()



class format_transaction_one_factor(object):
    def __init__(self, buy_para_name, sell_para_name):
        self.buy_para_name = buy_para_name
        self.sell_para_name = sell_para_name

    def cal_std_mean_from_returns(self, df, Buy_date, Sell_date):
        return_df = df[(df.Date >= Buy_date) & (df.Date <= Sell_date)]['Close'].pct_change()
        try:
            std = np.nanstd(return_df)
            mean = np.nanmean(return_df)
        except Exception:
            std = np.nan
            mean = np.nan
        return mean, std

    ### df is the csv file you use to backtest, use to calculate sharpe ratio
    def summary(self, detail_df):
        tp_xd = detail_df[self.sell_para_name].iloc[0]  ######################################################
        tp_xu = detail_df[self.buy_para_name].iloc[0]  #####################################################
        Avg_trans_return = round(detail_df['trans_return'].mean(), 4)
        Avg_daily_return = round(detail_df['daily_return'].mean(), 4)
        Avg_annual_return = round(detail_df['annual_return'].mean(), 4)
        total_period = int(detail_df['period'].sum())
        Avg_period = int(detail_df['period'].mean())
        win_time = len(detail_df[detail_df['trans_return'] > 0])
        loss_time = len(detail_df[detail_df['trans_return'] <= 0])
        total_time = win_time + loss_time
        win_percent = win_time / total_time
        detail_df['percent_value'] = detail_df['trans_return'] + 1
        cum_return = np.prod(detail_df['percent_value']).round(4)
        del detail_df['percent_value']
        try:
            geo_avg_daily_return = round(pow(cum_return, 1 / total_period), 5) - 1
            geo_avg_annual_return = round(pow(geo_avg_daily_return + 1, 365), 4) - 1
        except Exception:
            geo_avg_daily_return = np.nan
            geo_avg_annual_return = np.nan
        daily_risk_free_rate = round(pow(1.03, 1 / 365), 5) - 1
        total_std = np.sum(detail_df['std'] * detail_df['period']) / total_period
        try:
            sharpe_ratio = (geo_avg_daily_return - daily_risk_free_rate) / total_std
        except Exception:
            sharpe_ratio = np.nan
        summary = [tp_xd, tp_xu, Avg_trans_return, Avg_daily_return, Avg_annual_return, Avg_period, total_period,
                   cum_return, sharpe_ratio, geo_avg_daily_return, geo_avg_annual_return, win_time, loss_time,
                   total_time, win_percent]
        return summary


    def format_transaction_one_factor(self, results, commission, df):
        detail_df = pd.DataFrame()
        for i in range(len(results)):
            print (i)
            strats = results[i][0]
            tp_xd = strats.params.tp_xd
            tp_xu = strats.params.tp_xu
            pyfoliozer = strats.analyzers.getbyname('pyfolio')
            returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
            if len(transactions) <= 1:
                continue
            else:
                pass
            Buy_df = transactions[transactions['amount'] > 0]
            Buy_df['date'] = Buy_df.index
            Buy_df.index = np.arange(len(Buy_df))
            Buy_df.rename(columns={'date': 'Buy_date',
                                   'amount': 'Buy_amount',
                                   'price': 'Buy_price',
                                   'value': 'Buy_value'}, inplace=True)
            Sell_df = transactions[transactions['amount'] < 0]
            Sell_df['date'] = Sell_df.index
            Sell_df.index = np.arange(len(Sell_df))
            Sell_df.rename(columns={'date': 'Sell_date',
                                    'amount': 'Sell_amount',
                                    'price': 'Sell_price',
                                    'value': 'Sell_value'}, inplace=True)
            if len(Sell_df) == 0:
                continue
            else:
                pass
            transactions_df = pd.merge(Buy_df, Sell_df, left_index=True, right_index=True, how='left')
            transactions_df = transactions_df.dropna()
            transactions_df['std'] = transactions_df.apply(
                lambda row: self.cal_std_from_returns(df, row['Buy_date'], row['Sell_date'])[0], axis=1).round(5)
            transactions_df['std'] = transactions_df.apply(
                lambda row: self.cal_std_from_returns(df, row['Buy_date'], row['Sell_date'])[1], axis=1).round(5)
            transactions_df['tp_xd'] = tp_xd
            transactions_df['tp_xu'] = tp_xu
            detail_df = detail_df.append(transactions_df, ignore_index=True)

        detail_df['period'] = (detail_df['Sell_date'] - detail_df['Buy_date']).apply(lambda x: x.days)
        detail_df['Buy_comm'] = (abs(detail_df['Buy_value']) * commission).round(2)
        detail_df['Sell_comm'] = (abs(detail_df['Sell_value']) * commission).round(2)
        detail_df['net_profit'] = (detail_df['Buy_value'] + detail_df['Sell_value'] - \
                                   detail_df['Buy_comm'] - detail_df['Sell_comm']).round(2)
        detail_df['trans_return'] = (detail_df['net_profit'] / abs(detail_df['Buy_value'])).round(4)
        detail_df['daily_return'] = (pow(detail_df['trans_return'] + 1, 1 / detail_df['period'])).round(5) - 1
        detail_df['annual_return'] = (pow((1 + detail_df['daily_return']), 365)).round(4) - 1
        a = detail_df.groupby(['tp_xd', 'tp_xu'])
        summary_dict = a.apply(lambda x: self.summary(x))
        summary_df = pd.DataFrame(
            {'tp_xd': summary_dict.apply(lambda x: x[0]).values,  ####################################
             'tp_xu': summary_dict.apply(lambda x: x[1]).values,  #######################################
             'Avg_trans_return': summary_dict.apply(lambda x: x[2]).values,
             'Avg_daily_return': summary_dict.apply(lambda x: x[3]).values,
             'Avg_annual_return': summary_dict.apply(lambda x: x[4]).values,
             'Avg_period': summary_dict.apply(lambda x: x[5]).values,
             'total_period': summary_dict.apply(lambda x: x[6]).values,
             'cum_return': summary_dict.apply(lambda x: x[7]).values,
             'risk_adjusted_return': summary_dict.apply(lambda x: x[8]).values,
             'geo_avg_daily_return': summary_dict.apply(lambda x: x[9]).values,
             'geo_avg_annual_return': summary_dict.apply(lambda x: x[10]).values,
             'win_time': summary_dict.apply(lambda x: x[11]).values,
             'loss_time': summary_dict.apply(lambda x: x[12]).values,
             'total_time': summary_dict.apply(lambda x: x[13]).values,
             'win_percent': summary_dict.apply(lambda x: x[14]).values},
            columns=['tp_xd', 'tp_xu', 'Avg_trans_return',
                     'Avg_daily_return', 'Avg_annual_return', 'Avg_period', 'total_period',
                     'cum_return', 'risk_adjusted_return', 'geo_avg_daily_return', 'geo_avg_annual_return', 'win_time',
                     'loss_time', 'total_time', 'win_percent'],
            index=range(len(summary_dict))
            )

        detail_df['Buy_price'] = detail_df['Sell_price'].round(2)
        detail_df[['Buy_date', 'Sell_date']] = detail_df[['Buy_date', 'Sell_date']].applymap(
            lambda n: n.strftime('%Y-%m-%d'))
        del detail_df['symbol_y']
        detail_df.rename(columns={'symbol_x': 'symbol'}, inplace=True)
        col_order = ['tp_xd', 'tp_xu', 'symbol', 'Buy_amount', 'Buy_price', 'Buy_value', 'Buy_comm', 'Buy_date',
                     'Sell_amount',
                     'Sell_price', 'Sell_value', 'Sell_comm', 'Sell_date', 'period', 'std', 'net_profit',
                     'trans_return',
                     'daily_return', 'annual_return']
        detail_df = detail_df[col_order]
        return summary_df, detail_df


