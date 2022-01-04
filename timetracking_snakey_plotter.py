from collections import defaultdict
from plotly.offline import plot as plotlyplot
import plotly.graph_objects as plotlygo
from math import floor


def _mins_to_hours(mins):
    total_hours = floor(mins/60)
    remaining_minutes = int(mins-total_hours*60)
    return f"{total_hours}:{remaining_minutes:02d}"

def plot_timetracking_data(data):
    """ Plots the timetracking data as a snakey diagram.
    
    Does not return anything, but shows the resulting diagram in a new browser
    tab. Returns nothing. The plotting is done using *plotly*.

    Parameters
    ----------
    data : `dict` 
       Multilevel nested dictionary. On the first level is a category mapping:
          ``'@JOB' : [120.0, {2. level nested activity dict}]``
       On the second level there is activity tag mapping:
          ``'@Read' : [60.0, {3. level nested specifier dict}]``
       On the third level there is activity specifier tag mapping:
          ``'@Blogs' : 30.0``
       All durations are given in minutes.
      """
    sources = []
    targets = []
    values = []
    cat_labels = []
    act_labels = []
    spc_labels = []
    cat_mins = defaultdict(float) 
    act_mins = defaultdict(float) 

    for cat, cat_data in sorted(data.items()):
        cat_minutes, activities = cat_data
        cat_mins[cat]+=cat_minutes
        if not cat in cat_labels: cat_labels.append(cat)
        for act, act_data in sorted(activities.items()):
            act_minutes, _ = act_data
            if act_minutes>0:
                act_mins[act]+=act_minutes
                if not act in act_labels: act_labels.append(act)
                sources.append(cat)
                targets.append(act)
                values.append(act_minutes)
        
        for act, act_data in sorted(activities.items()):
            _, specifiers = act_data
            if not specifiers:
                specifiers["None specified"] = 1
            for spc, spc_minutes in sorted(specifiers.items()):
                spc_label = "specifier_"+spc
                if not spc_label in spc_labels: spc_labels.append(spc_label)
                sources.append(act)
                targets.append(spc_label)
                values.append(spc_minutes)
    
    labels = list(sorted(cat_labels)) +\
                list(sorted(act_labels)) +\
                list(sorted(spc_labels))
    label_dict = {y:x for x, y in enumerate(labels)}
    source_nodes = [label_dict[x] for x in sources]
    target_nodes = [label_dict[x] for x in targets]

    shown_labels = [cl.replace('@', '')+" "+_mins_to_hours(cat_mins[cl])
                        for cl in sorted(cat_labels)] +\
                    [al.replace('@', '')+" "+_mins_to_hours(act_mins[al])
                        for al in sorted(act_labels)] +\
                    [sl.replace('specifier_', '') for sl in list(sorted(spc_labels))]

    fig = plotlygo.Figure( data=[plotlygo.Sankey(
            node = {'label' : shown_labels},
            # This part is for the link information
            link = {'source': source_nodes,
                    'target': target_nodes,
                    'value': values})])

    # With this save the plots 
    plotlyplot(fig,
        image_filename='sankey_plot_1', 
        image='png', 
        image_width=1000, 
        image_height=600
    )
    # And shows the plot
    fig.show()