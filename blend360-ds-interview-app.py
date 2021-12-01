import streamlit as st
import pandas as pd
import numpy as np
import os
from sklearn import metrics
from datetime import timedelta, date
import collections
import matplotlib.pyplot as plt
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
from tempfile import NamedTemporaryFile
import shutil
import csv


st.set_page_config(page_title='Blend360 DS Interview Panel')

st.write("""
# Interview Panel Selection

This app helps you select interview panels to **balance** the interviewers work load.

""")

#st.sidebar.image("./Blend360Logo.svg", use_column_width=False)
#st.sidebar.title('BLEND360')



#Definition for strippping whitespace
def trim(dataset):
    trim = lambda x: x.strip() if type(x) is str else x
    return dataset.applymap(trim)

def header(url):
     st.markdown(f'<p style="background-color:#0066cc;color:#33ff33;font-size:24px;border-radius:2%;">{url}</p>', unsafe_allow_html=True)

def sidebar_header(url):
     st.sidebar.markdown(f'<p style="background-color:#0066cc;color:#33ff33;font-size:24px;border-radius:2%;">{url}</p>', unsafe_allow_html=True)

        
        
        
#data_path =".\data/"
data_path ="./"
interview_schedule = data_path + "interview.csv"
panel_list = data_path + "interview_panel_list.csv"


df_interview_schedule = trim(pd.read_csv(interview_schedule, dtype=str))
df_full_panel = trim(pd.read_csv(panel_list, dtype=str))


candidate_list = df_interview_schedule.Candidate.unique()
df_panel_list = df_full_panel.Interviewer.unique()
hiring_mgr_list = df_full_panel.Interviewer.unique()


###### Add Blend Logo
#st.sidebar.image("Blend360Logo.svg", width=100)


###### Collects user input features into dataframe
def user_input_features():   
    
    st.sidebar.header('Select Candidate Name:')
    candidate_name = st.sidebar.selectbox('Candidate Name',candidate_list).strip()

    
    st.sidebar.header('Select time window:')
    
    num_past_wks = st.sidebar.slider('Number of past weeks', -4,0,-2)
    num_future_wks = st.sidebar.slider('Number of future weeks', 0,4,2)
    
    data = {'candidate_name': candidate_name,
            'num_past_wks': num_past_wks,
            'num_future_wks': num_future_wks
            }
    features = pd.DataFrame(data, index=[0])
    return features
    
input_df = user_input_features()



##### Show results after filters

candidate_nm = input_df.iloc[0]['candidate_name']

rslt_df = df_interview_schedule[df_interview_schedule['Candidate'] == candidate_nm]
st.subheader('Candidate **' + str(candidate_nm) + '** interview panel:')
st.dataframe(data=rslt_df, width=900, height=100)
#st.write(rslt_df)
  
    

##### Summary by scheduled freq
today = date.today()
#st.write(today) 

first_num_days = int(input_df.iloc[0]['num_past_wks'] * 7)
last_num_days =  int(input_df.iloc[0]['num_future_wks'] * 7)

first_dt = date.today() + timedelta(days=first_num_days)
last_dt = date.today() + timedelta(last_num_days)


###### Date filter
df_interview_schedule['Interview Date']= pd.to_datetime(df_interview_schedule['Interview Date'], format='%Y-%m-%d').dt.date
#st.write(df_interview_schedule)


filter_df = df_interview_schedule[df_interview_schedule['Interview Date'] >= first_dt] 
filter_df = filter_df[filter_df['Interview Date'] <= last_dt] 
#st.write(filter_df)



#df = df_interview_schedule.drop(['Candidate', 'Hiring Manager','Interview Date'], axis=1)
df = filter_df.drop(['Candidate', 'Hiring Manager','Interview Date'], axis=1)


#df = df.apply(pd.value_counts).fillna(0)
#st.write(df)


list_of_names = df['Panel #1'].to_list()+df['Panel #2'].to_list()+df['Panel #3'].to_list()+df['Panel #4'].to_list()+df['Panel #5'].to_list()+df['Panel #6'].to_list()+df['Panel #7'].to_list()+df['Panel #8'].to_list()

while("NaN" in list_of_names) :
    list_of_names.remove("")

#st.write(list_of_names)
#count = collections.Counter(list_of_names)
#df = pd.DataFrame.from_dict(count, orient='index')
#df.plot(kind='bar')

df = pd.DataFrame({'Interviewer': list_of_names})
#st.write(df)


df_freq = df.groupby('Interviewer', as_index=False).size()
df_freq = df_freq.rename(columns={"size": "Number of times scheduled"})
df_freq = df_freq.sort_values('Number of times scheduled')
#st.dataframe(df_freq)


#### Merge with full interviews 
df_full_freq = pd.merge(left=df_full_panel, right=df_freq, how='left', left_on='Interviewer', right_on='Interviewer')

df_full_freq = df_full_freq.drop('Interviewer_Email', 1)
df_full_freq.fillna(0, inplace=True)
df_full_freq['Number of times scheduled'] = df_full_freq['Number of times scheduled'].astype(int)
df_full_freq = df_full_freq.sort_values('Number of times scheduled')





##### Select
st.subheader('Select Interviewers (Max 8) for '+str(candidate_nm)+ ':')
selected_interviewers = st.multiselect('The Intervewers are ranked by scheduled freq with the least freq on top:', df_full_freq.Interviewer)


interview_dt = st.date_input("Interview Date",date.today())
#st.write('Interview Date:', interview_dt)



##### Save selection
num_interviewers =len(selected_interviewers)
if(st.button("Update Panel")):
    if num_interviewers == 0:
        st.write('Please selected Interviewers!')  
    elif num_interviewers > 8:
        #st.write('You selected too many interviewers! Maximum 8!')
        header('You selected too many interviewers! Maximum 8!')
    else:
        #save/update the selection
        
        #num_interviewers
        for i in range(num_interviewers,8):
            selected_interviewers.append("")
            
        #st.write('### Selected Interviewers', selected_interviewers)

        candidate_nm = input_df.iloc[0]['candidate_name']
        
        filename = 'interview.csv'
        tempfile = NamedTemporaryFile(mode='w', delete=False)
        fields = ['Candidate','Hiring Manager','Interview Date','Panel #1','Panel #2','Panel #3','Panel #4','Panel #5','Panel #6','Panel #7','Panel #8']
        
        #with open(r'interview.csv', 'a', newline='') as csvfile:
        with open(filename, 'r') as csvfile, tempfile:
            
            reader = csv.DictReader(csvfile, fieldnames=fields)
            writer = csv.DictWriter(tempfile, fieldnames=fields)
            
            for row in reader:
                if row['Candidate'] == str(candidate_nm):
                    row['Interview Date'], row['Panel #1'], row['Panel #2'], row['Panel #3'], row['Panel #4'], row['Panel #5'], row['Panel #6'], row['Panel #7'], row['Panel #8'] = interview_dt, selected_interviewers[0], selected_interviewers[1], selected_interviewers[2], selected_interviewers[3], selected_interviewers[4], selected_interviewers[5], selected_interviewers[6], selected_interviewers[7]
                    
                row = {'Candidate': row['Candidate'], 'Hiring Manager': row['Hiring Manager'], 'Interview Date': row['Interview Date'], 'Panel #1': row['Panel #1'], 'Panel #2': row['Panel #2'], 'Panel #3': row['Panel #3'], 'Panel #4': row['Panel #4'], 'Panel #5': row['Panel #5'], 'Panel #6': row['Panel #6'], 'Panel #7': row['Panel #7'], 'Panel #8': row['Panel #8']}
                
                writer.writerow(row)
            
            
        shutil.move(tempfile.name, filename)

        #st.write('Interviewer panel is updated successfully! Refresh to see the change!')
        header('Interviewer panel is updated successfully! Refresh to see the change!')

#st.write(df_freq)
#st.dataframe(df_panel)



st.dataframe(data=df_full_freq, width=700, height=200)


#### PLOT
st.subheader('Interviewers load between ' + str(first_dt) + ' and ' + str(last_dt) + ':')
#st.write(date.datetime.strptime('10/25/2021', "%d%m%Y").date())

st.set_option('deprecation.showPyplotGlobalUse', False)

df_full_freq.sort_values(by='Number of times scheduled',ascending=False).plot.barh(x='Interviewer', y='Number of times scheduled')
plt.show()
st.pyplot()




##### Show the full scheduled data
st.subheader('Full Scheduled interviews:')

gb = GridOptionsBuilder.from_dataframe(df_interview_schedule)
gb.configure_pagination()
gb.configure_side_bar()
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
gridOptions = gb.build()
AgGrid(df_interview_schedule, gridOptions=gridOptions, enable_enterprise_modules=True)
    
    
    
    

##### Add a new Candidate with panel
def add_new_candidate():       
    st.sidebar.header('Add a new Candidate:')
    new_candidate_nm = st.sidebar.text_input('New Candidate Name:').strip() 
    new_hiring_mgr_nm = st.sidebar.selectbox('Hiring Manager:',hiring_mgr_list).strip() 

    data = {'new_candidate_nm': new_candidate_nm,
                'new_hiring_mgr_nm': new_hiring_mgr_nm,
           }
    features = pd.DataFrame(data, index=[0])
    return features
    
add_new_df = add_new_candidate()


### Save the new candidate
if(st.sidebar.button("Add a new candidate")):
    #st.write(add_new_df)    

    with open(r'interview.csv', 'a', newline='') as csvfile:
        fieldnames = ['Candidate','Hiring Manager']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writerow({'Candidate':add_new_df.iloc[0]['new_candidate_nm'], 'Hiring Manager':add_new_df.iloc[0]['new_hiring_mgr_nm']})
        
    #st.sidebar.write('The cadidate ' + str(add_new_df.iloc[0]['new_candidate_nm']) + ' is successfuly added! Refresh to see the change!')
    sidebar_header('The cadidate ' + str(add_new_df.iloc[0]['new_candidate_nm']) + ' is successfuly added! Refresh to see the change!')
    
##### Delete a Candidate


