# Network_visualization


github repository containing the code and result files for the RAAN internship program case study. 

In this project, a 2D and 3D visualization of a given network is presented. Furthermore, the results are presented in a web application that is also deployed online. 

The **python** libraries used are : 

- **networkx** for the network creation 
- **plotly** for the interactive visualization of the network 
- **dash** for creating the dashboard 

The application is hosted in **heroku** cloud application platform. 

### The application can be accessed in the following [link](https://network-case-study.herokuapp.com/)


## Reproducing the results: 

Create a conda environment and acitvate it with: 

``` 
conda create -n env_name python==3.8.3
conda activate env_name
```

Install the required libraries with: 

```
pip install -r requirements.txt 
```
Add the dataset in the same folder with the code. 
