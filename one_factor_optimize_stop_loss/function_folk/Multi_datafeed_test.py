# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import pandas as pd
import backtrader as bt
import numpy as np
from backtrader.feeds import GenericCSVData
import backtrader.indicators as btind
from backtrader import observers
import datetime
# from report import Cerebro
import csv


# Create a Stratey
class MyStrategy(bt.Strategy):
    params = (

    )
    # def start(self):
    #     self.mystats = open('data/mystats.csv', 'wb')
    #     self.mystats.write('trade_date, open,high, low, close, volume, vp, q_g, cash, value')

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        btind.SMA(self.data.vp, period=1, subplot=True)
        btind.SMA(self.data.q_g, period=1, subplot=True)
        # # Add a MovingAverageSimple indicator
        # self.ssa = ssa_index_ind(ssa_window=self.params.ssa_window, subplot=False)
        # # bt.indicator.LinePlotterIndicator(self.ssa, name='ssa')
        # self.sma = bt.indicators.SimpleMovingAverage(period=self.params.maperiod)

    # def start(self):
    #     print("the world call me!")

    # def prenext(self):
    #     print("not mature")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        # curdate =  self.datas[0].datetime.date(0)

        if not pd.to_datetime(self.datas[0].datetime.date(0)) == datetime.datetime(2014, 1, 2):
        # Check if we are in the market
            if not self.position:
                # Not yet ... we MIGHT BUY if ...
                if (self.data.tp_score[0] > 50) and (self.data.tp_score[-1] < 50):
                    print ('the today tp_Score is:{}'.format(str(self.data.tp_score[0])))
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    # self.log('BUY CREATE, %.2f' % self.dataclose[0])

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()
                    self.log('BUY CREATE, %.2f' % self.order.executed.price + 'tp: %.2f' % self.data.tp_score[0])

            else:

                if (self.data.tp_score[0] < 50) and (self.data.tp_score[-1] > 50):
                    # SELL, SELL, SELL!!! (with all possible default parameters)
                    # self.log('SELL CREATE, %.2f' % self.dataclose[0])

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.sell()
                    self.log('SELL CREATE, %.2f' % self.order.executed.price + 'tp: %.2f' % self.data.tp_score[0])
        else:
            pass


    # class Broker(observers.Observer):
    #     alias = ('CashValue',)
    #     lines = ('cash', 'value')
    #     plotinfo = dict(plot=True, subplot=True)
    #     def next(self):
    #         self.lines.cash[0] = self._owner.broker.getcash()
    #         self.lines.value[0] = self._owner.broker.getvalue()
    # def stop(self):
    #     items = [self.broker.startingcash, self.broker.getvalue()]
    #     b = open('result.csv', 'a', newline='')
    #     a = csv.writer(b)
    #     a.writerow(items)
    #     b.close()

    class BuySellObserver(observers.Observer):
        # alias = ('CashValue',)
        lines = ('buy', 'sell')
        # plotinfo = dict(plot=True, subplot=True)
        def next(self):
            self.lines.buy[0] = self._owner.broker.getcash()
            self.lines.sell[0] = self._owner.broker.getvalue()


def read_data():
    data_list = ['data/0700HK.csv',
                 'data/1888HK.csv',
                 'data/3883HK.csv']
    for path in data_list:
        data = bt.feeds.GenericCSV(dataname=path)
        cerebro.adddata(data)

if __name__ == '__main__':
    # Create a cerebro entity
    # cerebro = bt.Cerebro(writer=True, stdstats = False)
    cerebro = bt.Cerebro(writer=True)
    # Add a strategy
    cerebro.addstrategy(MyStrategy)

    data = GenericCSV_vp(
        dataname='data/700HK_qtv_final.csv',
    )
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.BuySell, barplot=False)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addobserver(bt.observers.Trades)
    # cerebro.addobserver(bt.observers.FundShares)
    cerebro.addobserver(bt.observers.TimeReturn)
    # Set our desired cash start
    cerebro.broker.setcash(1000000)
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    # Set the commission
    cerebro.broker.setcommission(commission=0)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')
    cerebro.addwriter(bt.WriterFile, csv=True, out='report/report_g_back_test.csv')
    # cerebro.add_order_history(orders)
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # Run over everything
    results = cerebro.run(stdstats=False)
    strat = results[0]
    print('SR:', strat.analyzers.SharpeRatio.get_analysis())
    print('DW:', strat.analyzers.DW.get_analysis())
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # cerebro.report('output/dir/for/your/report')
    cerebro.plot()