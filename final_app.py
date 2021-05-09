'''
RAAN Internship program case study
Nisioti Athina, Master Data Science, ETH Zurich, email: anisioti@student.ethz.ch
May 2021

The python libraries used for this project are:
networkx for the creation of the network
plotly for the visualization of the network
dash for creating the interactive dashboard that is deployed in the heroku cloud application platform.

'''
import dash #1.16.0
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd 
import numpy as np
import networkx as nx
import plotly.graph_objects as go
from base64 import b64encode
import io

buffer2d = io.StringIO() 
buffer3d=io.StringIO()

#### Importing the data ####
edges = pd.read_excel (r'raan_case_study interns.xlsx', sheet_name='edges')
nodes=pd.read_excel (r'raan_case_study interns.xlsx', sheet_name='nodes')
nodes=nodes.drop(columns="Unnamed: 3")

node_ids=list(set(nodes.node_id.values)) # the unique node_ids that are going to be used for creating the graph
#the number of unique nodes are:29
node_label=list(set(nodes.node_label.values)) 
#the number of unique label names are:29
node_colors=list(set(nodes.node_color.values)) 
#the number of unique color categories are:6


#### Creating the network ####
Gr_dir=nx.from_pandas_edgelist(edges, 'source_id', 'target_id', edge_attr=True, create_using=nx.DiGraph()) #directed graph 

atribs=nodes.set_index('node_id').to_dict('index') 
nx.set_node_attributes(Gr_dir, atribs)

### Define the edges that are bidirectional ###
double_edges=[]
for edge in Gr_dir.edges: 
    if Gr_dir.has_edge(edge[1], edge[0]):
        double_edges.append(edge)

'''
We observe that not all relations between the nodes are two-way, 
the network is not symmetric and therefore the direction will play an important role, 
since it gives information that we don't want to lose in our visualization.
'''

##### Create the 2-d visualization #####
#pos=nx.shell_layout(Gr_dir, scale=2)
pos=nx.circular_layout(Gr_dir, scale=2)
pos[966]=np.array([0,0])

'''
Since the node with id 966 has connections with all the nodes apart from one, it is manually added in the center. 
In that way this information is easily depicted and the plot looks better.
'''

for node in Gr_dir.nodes:
        Gr_dir.nodes[node]['pos'] = list(pos[node])

def create_edge_trace(edge, pos, is_bidirectional, showlegend=True):
    '''
    -edge: a tuple that contains the beginning and the ending of the edge of the graph 
    -pos: a dictionary with key the node_id and value the array of 2-d positions of the node
    -is bidirectional: True if the edge is bidirectional False otherwise 
    -showlegend: True if we want the trace to be shown in the legend
    
    Returns: 
    -an edge trace to be used in the 2-d plot
    The opacity and width of the edge are relative to the edge weight
    The bidirected edges are coloured in red while the one-way relations are blue. 
    -the color of the edge 
    '''
    x0, y0 = Gr_dir.nodes[edge[0]]['pos']
    x1, y1 = Gr_dir.nodes[edge[1]]['pos']
    weight = Gr_dir[edge[0]][edge[1]]['weights']
    opacity= weight/np.max(list(nx.get_edge_attributes(Gr_dir,'weights').values())) #normalize between 0 and 1
    if is_bidirectional==True: 
        color='red'
        legendgroup='red'
        name='Two-way Edge'
    else: 
        color='cornflowerblue'
        legendgroup='blue'
        name= 'One-way Edge'
    return go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
                        mode='lines',
                        line={'width': 10*weight/np.max(list(nx.get_edge_attributes(Gr_dir,'weights').values())), 'color': color},
                        line_shape='spline',
                        legendgroup=legendgroup,
                        name=name,
                        hoverinfo=None,
                        opacity=opacity, showlegend= showlegend), color




edge_trace=[]
edge_col=[]
for edge in Gr_dir.edges:
    if edge in double_edges: 
        if 'red' in edge_col: #we only want to create one legend signal for each edge
            trace,_= create_edge_trace(edge, pos, is_bidirectional = True, showlegend=False)
            edge_trace.append(trace)
        else: 
            trace,col= create_edge_trace(edge, pos, is_bidirectional = True, showlegend=True) 
            edge_col.append(col)
            edge_trace.append(trace)
    else:
        if 'cornflowerblue' in edge_col:
            trace,_= create_edge_trace(edge, pos, is_bidirectional = False, showlegend=False)
            edge_trace.append(trace)
        else:
            trace,col= create_edge_trace(edge, pos, is_bidirectional = False, showlegend=True) 
            edge_col.append(col)
            edge_trace.append(trace)



def create_node_trace(node, pos, showlegend= True):
    '''
    -node: the node id
    -pos: the position coordinates of the node in the plot
    -showlegend: True if we want to the trace to take part in the legend False otherwise
    
    Returns: 
    -trace of the node to be used in the figure
    -color of the node 
    '''
    x_node=pos[node][0]
    y_node=pos[node][1]
    color=Gr_dir.nodes[node]['node_color']
    label=Gr_dir.nodes[node]['node_label']
    return go.Scatter(x=[x_node,None],
                      y=[y_node,None],
                      mode='markers',
                      marker=dict(symbol='circle',size=20,color=color),#color the nodes according to their community
                      legendgroup=str(color),
                      name=str(color),
                      showlegend= showlegend,
                      text=label, #label according to the node label
                      hoverinfo='text'), color



node_trace=[]
colors_used=[]
for node in Gr_dir.nodes:
    if Gr_dir.nodes[node]['node_color'] in colors_used: #if already used before don't show it in the legend, just group it with it
        trace,_ = create_node_trace(node, pos, False)
        node_trace.append(trace)
    else: 
        trace, color = create_node_trace(node, pos, True)
        node_trace.append(trace)
        colors_used.append(color)

### Create the middle nodes for adding the edge annotations ### 
'''
Since plotly doesn't allow for text annotation in the edges, 
create nodes that are invisible in the middle of the edges where we can find the text providing information about the edges.
'''
middle_trace = go.Scatter(x=[], y=[], hovertext=[], mode='markers', hoverinfo="text",
                                    marker={'size': 20, 'color': 'LightSkyBlue'},
                                    opacity=0, showlegend= False)


for edge in Gr_dir.edges:
    x0, y0 = Gr_dir.nodes[edge[0]]['pos']
    x1, y1 = Gr_dir.nodes[edge[1]]['pos']
    if edge in double_edges:
        edge_text = "Bidirectional edge:" + "<br>" + str(Gr_dir.nodes[edge[0]]['node_label']) + " To: " + str(Gr_dir.nodes[edge[1]]['node_label'])  + ", weight: " + str(Gr_dir.edges[edge]['weights'])+"<br>" + str(Gr_dir.nodes[edge[1]]['node_label']) + " To: " + str(Gr_dir.nodes[edge[0]]['node_label'])  + ", weight: " + str(Gr_dir.edges[(edge[1], edge[0])]['weights'])
    else:
        edge_text="From: " + str(Gr_dir.nodes[edge[0]]['node_label']) + " To: " + str(Gr_dir.nodes[edge[1]]['node_label']) + ", weight: " + str(Gr_dir.edges[edge]['weights'])
    hovertext= edge_text
    middle_trace['x'] += tuple([(x0 + x1) / 2])
    middle_trace['y'] += tuple([(y0 + y1) / 2])
    middle_trace['hovertext'] += tuple([hovertext])
   
#the layout of the plot 
layout=go.Layout(title='Network 2-d visualization', showlegend=True, hovermode='closest',
                            margin={'b': 60, 'l': 60, 'r': 60, 't': 60},
                            xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                            yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                            height=600,
                            clickmode='event+select',
                            annotations=[
                                dict(
                                    ax=(Gr_dir.nodes[edge[0]]['pos'][0] + Gr_dir.nodes[edge[1]]['pos'][0]) / 2,
                                    ay=(Gr_dir.nodes[edge[0]]['pos'][1] + Gr_dir.nodes[edge[1]]['pos'][1]) / 2, axref='x', ayref='y',
                                    x=(Gr_dir.nodes[edge[1]]['pos'][0] * 3 + Gr_dir.nodes[edge[0]]['pos'][0]) / 4,
                                    y=(Gr_dir.nodes[edge[1]]['pos'][1] * 3 + Gr_dir.nodes[edge[0]]['pos'][1]) / 4, xref='x', yref='y',
                                    showarrow=True,
                                    arrowhead=3,
                                    arrowsize=4,
                                    arrowwidth=1,
                                    arrowcolor='red' if edge in double_edges else 'cornflowerblue',
                                    opacity=0.7
                                ) for edge in Gr_dir.edges]
                            )


fig_2d = go.Figure(layout=layout)

for trace in edge_trace:
    fig_2d.add_trace(trace)

for trace in node_trace:
    fig_2d.add_trace(trace)

fig_2d.add_trace(middle_trace)
fig_2d.update_layout(legend_itemclick=False)
fig_2d.update_layout(legend_itemdoubleclick=False)
fig_2d.write_html(buffer2d)

###Start with the 3-d visualization###
pos3d = nx.kamada_kawai_layout(Gr_dir,dim=3, weight= 'weights')

for node in Gr_dir.nodes:
        Gr_dir.nodes[node]['pos3d'] = list(pos3d[node])

def create_edge_trace3d(edge, pos, is_bidirectional, showlegend=True):
    '''
    -edge: a tuple that contains the beginning and the ending of the edge of the graph 
    -pos: a dictionary with key the node_id and value the array of 3-d positions of the node
    -is bidirectional: True if the edge is bidirectional False otherwise 
    -showlegend: True if we want the trace to be shown in the legend
    
    Returns: 
    -an edge trace to be used in the 3-d plot
    The opacity and width of the edge are relative to the edge weight
    The bidirected edges are coloured in red while the one-way relations are blue. 
    -the color of the edge 
    '''
    x0, y0, z0 = Gr_dir.nodes[edge[0]]['pos3d']
    x1, y1, z1 = Gr_dir.nodes[edge[1]]['pos3d']
    weight = Gr_dir[edge[0]][edge[1]]['weights']
    opacity= weight/np.max(list(nx.get_edge_attributes(Gr_dir,'weights').values())) #normalize between 0 and 1
    if is_bidirectional==True: 
        color='red'
        legendgroup='red'
        name='Two-way Edge'
    else: 
        color='cornflowerblue'
        legendgroup='blue'
        name= 'One-way Edge'
    return go.Scatter3d(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]), z=tuple([z0,z1,None]),
                        mode='lines',
                        line={'width': 10*weight/np.max(list(nx.get_edge_attributes(Gr_dir,'weights').values())), 'color': color},
                        legendgroup=legendgroup,
                        name=name,
                        hoverinfo=None,
                        opacity=opacity, showlegend= showlegend), color


edge_trace3d=[]
edge_col=[]
for edge in Gr_dir.edges:
    if edge in double_edges: 
        if 'red' in edge_col:
            trace,_= create_edge_trace3d(edge, pos3d, is_bidirectional = True, showlegend=False)
            edge_trace3d.append(trace)
        else: 
            trace,col= create_edge_trace3d(edge, pos3d, is_bidirectional = True, showlegend=True) 
            edge_col.append(col)
            edge_trace3d.append(trace)
    else:
        if 'cornflowerblue' in edge_col:
            trace,_= create_edge_trace3d(edge, pos3d, is_bidirectional = False, showlegend=False)
            edge_trace3d.append(trace)
        else:
            trace,col= create_edge_trace3d(edge, pos, is_bidirectional = False, showlegend=True) 
            edge_col.append(col)
            edge_trace3d.append(trace)


def create_node_trace3d(node, pos, showlegend= True):
    '''
    -node: the node id
    -pos: the position coordinates of the node in the plot
    -showlegend: True if we want to the trace to take part in the legend False otherwise
    
    Returns: 
    -trace of the node to be used in the figure
    -color of the node 
    '''
    x_node=pos[node][0]
    y_node=pos[node][1]
    z_node=pos[node][2]
    color=Gr_dir.nodes[node]['node_color']
    label=Gr_dir.nodes[node]['node_label']
    return go.Scatter3d(x=[x_node,None],
                      y=[y_node,None],
                      z=[z_node,None],
                      mode='markers',
                      marker=dict(symbol='circle',size=20,color=color),#color the nodes according to their community
                      legendgroup=str(color),
                      name=str(color),
                      showlegend= showlegend,
                      text=label, #label according to the node label
                      hoverinfo='text'), color


node_trace3d=[]
colors_used=[]
for node in Gr_dir.nodes:
    if Gr_dir.nodes[node]['node_color'] in colors_used: #if already used before don't show it in the legend, just group it with it
        trace,_ = create_node_trace3d(node, pos3d, False)
        node_trace3d.append(trace)
    else: 
        trace, color = create_node_trace3d(node, pos3d, True)
        node_trace3d.append(trace)
        colors_used.append(color)

middle_trace3d = go.Scatter3d(x=[], y=[],z=[], hovertext=[], mode='markers', hoverinfo="text",
                                    marker={'size': 20, 'color': 'LightSkyBlue'},
                                    opacity=0, showlegend= False)


for edge in Gr_dir.edges:
    x0, y0,z0 = Gr_dir.nodes[edge[0]]['pos3d']
    x1, y1,z1 = Gr_dir.nodes[edge[1]]['pos3d']
    
    if edge in double_edges:
        edge_text = "Bidirectional edge:" + "<br>" + str(Gr_dir.nodes[edge[0]]['node_label']) + " To: " + str(Gr_dir.nodes[edge[1]]['node_label'])  + ", weight: " + str(Gr_dir.edges[edge]['weights'])+"<br>" + str(Gr_dir.nodes[edge[1]]['node_label']) + " To: " + str(Gr_dir.nodes[edge[0]]['node_label'])  + ", weight: " + str(Gr_dir.edges[(edge[1], edge[0])]['weights'])
    else:
        edge_text="From: " + str(Gr_dir.nodes[edge[0]]['node_label']) + " To: " + str(Gr_dir.nodes[edge[1]]['node_label']) + ", weight: " + str(Gr_dir.edges[edge]['weights'])
    hovertext= edge_text
    middle_trace3d['x'] += tuple([(x0 + x1) / 2])
    middle_trace3d['y'] += tuple([(y0 + y1) / 2])
    middle_trace3d['z'] += tuple([(z0 + z1) / 2])
    middle_trace3d['hovertext'] += tuple([hovertext])

axis = dict(showbackground=False,
            showline=False,
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            title='')
#the layout of the plot: 
layout3d = go.Layout(title="The network 3-d visualization",
                margin={'b': 60, 'l': 60, 'r': 60, 't': 60},
                #width=1000,
                height=600,
                #clickmode='event+select',
                showlegend=True,
                scene=dict(xaxis=dict(axis),
                yaxis=dict(axis),
                zaxis=dict(axis)),
                #margin=dict(t=100),
                hovermode='closest')

fig3d = go.Figure(layout=layout3d)

for trace in edge_trace3d:
    fig3d.add_trace(trace)

for trace in node_trace3d:
    fig3d.add_trace(trace)
    
fig3d.add_trace(middle_trace3d)
fig3d.update_layout(legend_itemclick=False)
fig3d.update_layout(legend_itemdoubleclick=False)

fig3d.write_html(buffer3d)





##used for creating the different buttons for downloading the plots 
html_bytes2d = buffer2d.getvalue().encode()
encoded2d = b64encode(html_bytes2d).decode()

html_bytes3d = buffer3d.getvalue().encode()
encoded3d = b64encode(html_bytes3d).decode()

markdown_text = '''
**Export the plot in HTML format**
'''
markdown_description= '''

**USEFUL INFORMATION:**

In this app  the 2D and 3D visualization of a given network are presented. 
To find them just navigate through the tabs by clicking on the desired tab. 
If desired, the plots can be downloaded to html format by clicking on the button on the bottom left of the page. 

For the creation of the graph the python library ```networkx``` was used. 
For the visualization of the graphs the python library ```plotly```  was used. 
Finally, the web application was created by ```dash``` python library and is hosted in  ```heroku```  cloud application platform. 

After the eploratory analysis of the data there are some interesting points that are worth being mentioned, 
that also played an important role in the method used. 

- The dataset consists of 29 nodes, which are labelled uniquely and colored with 6 different colors (for the plot it is assumed that the colors 
correspond to different hypothetical categories)

- The edges between the nodes, have either one-way directed relations or are bidirected. Therefore, a directed graph is used. 
For the shake of better visualization of the relation types different color is used for edges that present one-way or two-way relations. 

- It is worth observing that all edges apart from one have as source or target node the node with id 966 (Antony). This led in the choice of 
circular layout when creating the 2D- plot. In that way all these nodes are equidistant from the central node (manually chosen to be node 966), 
and therefore distances do not present useful information in this plot. 

- Different edges have different width and opacity in their presentation in the plot. These parameters are relative to the weights of the edges.

- The direction of the edges, while also the corresponding weight can be seen by clicking in the middle of the edge. The labels of the nodes 
can be seen by clicking in the nodes. 

- For the 3D plot the Kamada-Kawai layout provided by networkx library was used, since most other layouts are not supported in 3D. 

- For better exploring the 3D plot, zooming in and rotating the plot is recommended. This can be done by the corresponding keys that exist above
the legend of the plot. 

- In my opinion, the 2D plot is more informative, as all the important relations are easily seen. But from the 3D plot, we can also observe the
relations between the nodes and the different types of the edges. What is nice observing is that the bidirectional edges are close together in the plot. 



'''

###Now the dash with tabs### 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#FBFCFC',
    'text': '#641E16'
}

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Introduction', children=[
        html.H1(children='RAAN Internship Program Case Study',
                 style={'textAlign': 'center',
                        'color': colors['text']}),
        html.H2(children='Nisioti Athina, Master Data Science, ETH Zurich, email: anisioti@student.ethz.ch',
                 style={'textAlign': 'center',
                        'color': colors['text']}),
        html.H3(children='May 2021',
                 style={'textAlign': 'center',
                        'color': colors['text']}),
        dcc.Markdown(children=markdown_description)]),


        dcc.Tab(label='2D plot', children=[
        html.H1(children='2D visualization of the Network',
                 style={'textAlign': 'center',
                        'color': colors['text']}),
        html.Div(children='The following figure shows the 2D plot of the given network. ', style={
                 'textAlign': 'left',
                'color': colors['text']}),
        html.P(children='Nodes are assinged to colors corresponding to a specific hypothetical property',style={
            'textAlign': 'left',
            'color': colors['text']} ),
        html.P(children='Edges can be bidirected or not',
               style={'textAlign': 'left',
                      'color': colors['text']} ),
        dcc.Graph(
            figure=fig_2d), 
       # download the html file of the plot
        dcc.Markdown(children=markdown_text),
        html.A(
        html.Button("Download HTML"), 
        id="download_html",
        href="data:text/html;base64," + encoded2d,
        download="2dvisualization.html")] ),

        dcc.Tab(label='3D-plot', children=[
        html.H1(children='3D visualization of the network',
                 style={'textAlign': 'center',
                        'color': colors['text']}),
        html.Div(children='The following figure shows the 3D plot of the given network. ', style={
                 'textAlign': 'left',
                'color': colors['text']}),
        html.P(children='Nodes are assinged to colors corresponding to a specific hypothetical property',style={
            'textAlign': 'left',
            'color': colors['text']} ),
        html.P(children='Edges can be bidirected or not',
               style={'textAlign': 'left',
                      'color': colors['text']} ),
            
            
        dcc.Graph(figure=fig3d),
        
        #download the html file of the plot
        dcc.Markdown(children=markdown_text),
        html.A(
        html.Button("Download HTML"), 
        id="download_html3d",
        href="data:text/html;base64," + encoded3d,
        download="3dvisualization.html")])
        
        
         ])
])


if __name__ == '__main__':
    app.run_server(debug=True)



