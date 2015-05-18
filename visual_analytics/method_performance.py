"""
detailed bar plot to measure the performance of different methods 

Usage: 

    >>from visual_analytics import method_performance as mp 
    >>fname = '29_org_base_0.5_acc.pickle'

    >>diff_methods, eval_perf, test_perf = mp.get_data(fname) 
    >>mp.single_perf_barplot(eval_perf, diff_methods, 'acc_ev.pdf', 'acceptor splice site') 
    >>mp.single_perf_barplot(test_perf, diff_methods, 'acc_te.pdf', 'acceptor splice site') 

Requirement:
    pylab: 
    pandas: 
"""

from __future__ import division
from collections import defaultdict
import numpy as np 
import pandas as pd 


def best_global_param_idx(data, methods=None, org_names=None):
    """
    for each method, report best param (averaged over orgs) based on eval data
    """

    if methods is None:
        methods = data.keys()

    if org_names is None:
        org_names = data[methods[0]][0].keys()

    best_param_method = {}
    best_test_method = {}

    inner_shape = data[methods[0]][0][org_names[0]].shape
    assert inner_shape == data[methods[0]][1][org_names[0]].shape

    for m in methods:
        all_num = np.zeros((len(org_names), inner_shape[0], inner_shape[1]))
        all_num_test = np.zeros((len(org_names), inner_shape[0], inner_shape[1]))

        for i,n in enumerate(org_names):
            assert data[m][0][n].shape == inner_shape
            all_num[i] = data[m][0][n]
            all_num_test[i] = data[m][1][n]
 
        # average over orgs and splits   
        mean_perf = all_num.mean(axis=1).mean(axis=0)
        assert len(mean_perf) == inner_shape[1]
        best_param_idx_eval = np.argmax(mean_perf)
        best_param_method[m] = best_param_idx_eval
        
        best_test_method[m] = all_num_test.mean(axis=1).mean(axis=0)[best_param_idx_eval]

    return best_param_method, best_test_method


def best_org_param_idx(filename, diff_methods=None, org_names=None):
    """
    for each method and org, report best param
    """

    import bz2
    import cPickle

    fh = bz2.BZ2File(filename, 'rb')
    data = cPickle.load(fh) 

    if diff_methods is None:
        diff_methods = data.keys()

    methods = ['individual', 'union', 'mtl', 'mtmkl'] ## pre-defined methods for learning techniques 
    assert (set(methods)==set(diff_methods)), "methods from pickle file %s != %s" % (diff_methods, methods)

    if org_names is None:
        org_names = data[methods[0]][0].keys()
    
    best_param_method_org = defaultdict(dict)
    all_num_eval = np.zeros((len(methods), len(org_names)))
    all_num_test = np.zeros((len(methods), len(org_names)))
    
    for m_idx, m in enumerate(methods):
        for n_idx, n in enumerate(org_names):
            best_param_idx = np.argmax(data[m][0][n].mean(axis=0))
            best_param_method_org[m][n] = best_param_idx
            all_num_eval[m_idx, n_idx] = data[m][0][n].mean(axis=0)[best_param_idx]
            all_num_test[m_idx, n_idx] = data[m][1][n].mean(axis=0)[best_param_idx]

        print m, all_num_test[m_idx].mean(), all_num_eval[m_idx].mean()

    # create pandas structures
    df_eval = pd.DataFrame(all_num_eval, columns=org_names, index=methods)
    df_test = pd.DataFrame(all_num_test, columns=org_names, index=methods)

    # df_eval.plot(kind="bar")
    # 

    #TODO: return all_num_*
    return df_eval, df_test


def multi_argmax_perf_barplot(df_eval_perf, df_test_perf, res_file, plot_title="", ylabel="auROC"):
    """
    argmax of org specific cv
    """
    import pylab 


def argmax_perf_barplot(df_eval_perf, df_test_perf, res_file, plot_title="", ylabel="auROC"):
    """
    argmax of org specific cv
    """
    import pylab 
    import numpy 

    pylab.figure(figsize=(10, 10)) # custom form 
    pylab.rcParams.update({'figure.autolayout': True}) # to fit the figure in canvas 

    width = 0.20
    separator = 0.10
    offset = 0
    used_colors = ["#88aa33", "#9999ff", "#ff9999", "#34A4A8"]
    xlocations = []
    min_max = [] 
    mean_perf = defaultdict(list) 
    num_methods = 0 
    labels = [] 
    
    methods = ['individual', 'union', 'mtl', 'mtmkl'] 
    #import ipdb; ipdb.set_trace()

    for org, perf in df_eval_perf.iteritems():
        num_methods = len(perf)
        offset += separator
        xlocations.append(offset + (width*(num_methods*1))/3)
        labels.append(org)
        rects = [] 
        
        for idx, meth in enumerate(methods):
            min_max.append(perf[meth])
            mean_perf[meth].append(perf[meth]) 

            rects.append(pylab.bar(offset, perf[meth], width, color=used_colors[idx], edgecolor='white'))

            offset += width 
    
    ## the mean perf bar 
    rects_avg = [] 
    offset += separator
    xlocations.append(offset + (width*(num_methods*1))/3)

    for idx, meth in enumerate(methods):
        rects_avg.append(pylab.bar(offset, sum(mean_perf[meth])/len(labels), width, color = used_colors[idx], edgecolor='white'))
        offset += width 

    offset += separator
    labels.append('Mean')

    ## modifying the image boarders 
    min_max.sort() 
    ymax = min_max[-1]*1.1
    ymin = min_max[0]*0.9

    # set ticks
    tick_step = 0.05
    ticks = [tick_step*i for i in xrange(round(ymax/tick_step)+1)]

    pylab.yticks(ticks)
    pylab.xticks(xlocations, labels, rotation="vertical") 

    fontsize=15
    ax = pylab.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_fontsize(fontsize)

    pylab.xlim(0, offset)
    pylab.ylim(ymin, ymax)
    
    pylab.title(plot_title)
    pylab.gca().get_xaxis().tick_bottom()
    pylab.gca().get_yaxis().tick_left()

    pylab.gca().get_yaxis().grid(True)
    pylab.gca().get_xaxis().grid(False)

    pylab.legend(tuple(rects), tuple(methods))
    pylab.ylabel(ylabel, fontsize = 15)
    pylab.savefig(res_file) 



def single_perf_barplot(data, methods, res_file, plot_title="", ylabel="auROC"):
    """
    visualizing the experiment result of different methods 
    
    @args data: data to plot, for each organism different methods and its performances
    @type data: <defaultdict<org_name:[(method, list)]>
    @args methods: different experiment methods 
    @type methods: list
    @args res_file: result file name 
    @type res_file: str
    """
    import pylab 
    import numpy 

    labels = data.keys()
    pylab.figure(figsize=(10, 10)) # custom form 
    #pylab.figure(figsize=(len(labels), (len(labels)/8)*5)) # 40, 10 # for 10 organisms 
    pylab.rcParams.update({'figure.autolayout': True}) # to fit the figure in canvas 

    width = 0.20
    separator = 0.15
    offset = 0
    num_methods = len(methods)
   
    ## FIXME catch colour according to the method 
    used_colors = ["#88aa33", "#9999ff", "#ff9999", "#34A4A8"]
    xlocations = []
    
    min_max = [] 
    mean_perf = defaultdict(list) 

    for org_name, details in data.items():
        offset += separator
        rects = [] 

        #xlocations.append(offset + (width*(num_methods*7+2))/2)
        xlocations.append(offset + (width*(num_methods*1))/3)

        for idx, bundles in enumerate(details):
            method, perfs = bundles 
            print '\t', method

            best_c = [] 
            for method_perf in perfs: 
                best_c.append(method_perf)
            best_c.sort() 

            min_max.append(best_c[-1])
            mean_perf[method].append(best_c[-1]) # best/highest c score over organisms on each method 

            #best_c = numpy.mean(perfs) 
            #min_max.append(best_c)
            #mean_perf[method].append(best_c) # best c over organisms on each method 

            rects.append(pylab.bar(offset, best_c[-1], width, color=used_colors[idx], edgecolor='white'))
            #rects.append(pylab.bar(offset, best_c, width, color=used_colors[idx], edgecolor='white'))
            offset += width 

        #offset += separator
        #break
   
    # average of each methods  
    rects_avg = [] 
    offset += separator
    xlocations.append(offset + (width*(num_methods*1))/3)
    
    for idx, meth in enumerate(methods):
        #rects_avg.append(pylab.bar(offset, round(sum(mean_perf['individual'])/len(labels), 2), width, color = used_colors[0], edgecolor='white'))
        rects_avg.append(pylab.bar(offset, sum(mean_perf[meth])/len(labels), width, color = used_colors[idx], edgecolor='white'))
        offset += width 

    print 'individual - mean perf', round(sum(mean_perf['individual'])/len(labels), 2)
    print 'union - mean perf', round(sum(mean_perf['union'])/len(labels), 2)
    print 'mtl - mean perf', round(sum(mean_perf['mtl'])/len(labels), 2)
    print 'mtmkl - mean perf', round(sum(mean_perf['mtmkl'])/len(labels), 2) 

    offset += separator
    labels.append('Mean')

    # determine the extreams 
    min_max.sort() 
    ymax = min_max[-1]*1.1
    ymin = min_max[0]*0.9

    # set ticks
    tick_step = 0.05
    ticks = [tick_step*i for i in xrange(round(ymax/tick_step)+1)]

    pylab.yticks(ticks)
    pylab.xticks(xlocations, labels, rotation="vertical") 

    fontsize=17
    ax = pylab.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_fontsize(fontsize)

    pylab.xlim(0, offset)
    pylab.ylim(ymin, ymax)
    
    pylab.title(plot_title)
    pylab.gca().get_xaxis().tick_bottom()
    pylab.gca().get_yaxis().tick_left()

    pylab.gca().get_yaxis().grid(True)
    pylab.gca().get_xaxis().grid(False)

    #pylab.legend(tuple(rects[0:21:7]), tuple(methods))
    pylab.legend(tuple(rects), tuple(methods))

    pylab.ylabel(ylabel, fontsize = 15)
    pylab.savefig(res_file) 


def get_data(filename):
    """
    process the pickle file to get data frames

    @args filename: pickle file from experiment run 
    @type filename: bz2 pickle file 

    retuns methods_name, evaluation performance and test performance
    """
    
    import bz2 
    import cPickle 

    fh = bz2.BZ2File(filename, 'rb')
    myobj = cPickle.load(fh) 

    methods = [] 
    eval_perf_tmp = defaultdict(list) 
    test_perf_tmp = defaultdict(list) 

    for method, org_perf in myobj.items():
        methods.append(method) 

        for name, perf_meas in org_perf[0].items():## eval performance  
            eval_perf_tmp[name].append((method, perf_meas.mean(axis=0)))# organme - method - mean of performance measure from different cross validation
        for name, test_meas in org_perf[1].items():## test performance 
            test_perf_tmp[name].append((method, test_meas.mean(axis=0)))
    fh.close()

    diff_methods = ['individual', 'union', 'mtl', 'mtmkl'] ## pre-defined methods for learning techniques 
    assert (set(methods)==set(diff_methods)), "methods from pickle file %s != %s" % (methods, diff_methods)

    # making an order for the experiments -  orgname - method - performance measure 
    eval_perf = defaultdict(list)
    test_perf = defaultdict(list)

    for order_meth in diff_methods:
        for org in eval_perf_tmp.keys():
            for methods in eval_perf_tmp[org]:
                if methods[0] == order_meth:
                    eval_perf[org].append(methods)

        for org in test_perf_tmp.keys():
            for methods in test_perf_tmp[org]:
                if methods[0] == order_meth:
                    test_perf[org].append(methods)

    return diff_methods, eval_perf, test_perf 


def mean_plot_diff_run(data_dir, res_file, signal="cleave signal"):
    """
    visualizing mean performance from different experiments

    @args data_dir: experiment path 
    @type data_dir: str 
    @args alpha: different parameter value 
    @type alpha: list 
    """
    
    import os 
    import re 

    file_mean = defaultdict(list) 
    for file in os.listdir(data_dir):
        #FIXME adjust the next line to get the name from the file name  
        #prefix = re.search('5.org_(\d+)_cleave.pickle', file).group(1) 
        prefix = re.search('5.org_(.+)_cleave.pickle', file).group(1) 
        
        mean_perf = defaultdict(list) 
        organisms, diff_methods, perfomance = data_process("%s/%s" % (data_dir, file)) 

        for org_name, details in perfomance.items():
            for idx, bundles in enumerate(details):
                method, perfs = bundles 
                #print '\t', method

                best_c = [] 
                for method_perf in perfs: 
                    best_c.append(method_perf)

                best_c.sort() 
                #min_max.append(best_c[-1])
                mean_perf[method].append(best_c[-1]) # best c over organisms on each method 
        
        file_mean[prefix].append(sum(mean_perf['union'])/len(organisms)) 
        file_mean[prefix].append(sum(mean_perf['individual'])/len(organisms)) 
        file_mean[prefix].append(sum(mean_perf['mtl'])/len(organisms)) 

    ## plotting function 
    import pylab 

    pylab.figure(figsize=(5, 10)) # custom form 
    #pylab.figure(figsize=(len(labels), (len(labels)/8)*5)) # 40, 10 # for 10 organisms 
    pylab.rcParams.update({'figure.autolayout': True}) # to fit the figure in canvas 

    width = 0.20
    separator = 0.15

    offset = 0
    num_methods = len(diff_methods)
    
    used_colors = ["#88aa33", "#9999ff", "#ff9999", "#34A4A8"]
    xlocations = []
    min_max = [] 
    for parameter, mean_meth_perf in sorted(file_mean.items()):
        offset += separator
        rects = [] 

        xlocations.append(offset + (width*(num_methods*1))/3)
        for idx, nb in enumerate(mean_meth_perf):
            min_max.append(nb)
            rects.append(pylab.bar(offset, nb, width, color=used_colors[idx], edgecolor='white'))
            offset += width 

    offset += separator
            
    min_max.sort() 
    ymax = min_max[-1]*1.1
    ymin = min_max[0]*0.9

    tick_step = 0.05
    ticks = [tick_step*i for i in xrange(round(ymax/tick_step)+1)]
    pylab.yticks(ticks)
    labels = ['df=%s' % x for x in sorted(file_mean.keys())]
    pylab.xticks(xlocations, labels, rotation="vertical") 

    fontsize=17
    ax = pylab.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_fontsize(fontsize)

    pylab.xlim(0, offset)
    pylab.ylim(ymin, ymax)
    
    plot_title = signal 
    pylab.title(plot_title)
    pylab.gca().get_xaxis().tick_bottom()
    pylab.gca().get_yaxis().tick_left()

    pylab.gca().get_yaxis().grid(True)
    pylab.gca().get_xaxis().grid(False)
    pylab.legend(tuple(rects), tuple(diff_methods))

    ylabel = "auROC"
    pylab.ylabel(ylabel, fontsize = 15)
    pylab.savefig(res_file) 


if __name__=="__main__":
    fname = "4K_db_labels/09_org_pn2_mtl_2-df/10org_mtmkl_pn_2_mtl_df-2_tss.pickle"
    eval, test = best_org_param_idx(fname)
    argmax_perf_barplot(eval, test, "test_4k_argmax.pdf")
