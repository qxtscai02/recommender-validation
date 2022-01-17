import streamlit as st
st.set_page_config(layout='wide')
import json
import s3fs
import random
import copy
FS = s3fs.S3FileSystem(anon=False)
import gspread

@st.cache
def load(configpath, testdatapath):
    with FS.open(configpath) as f:
        config = json.loads(f.read())
    user2domain = {v:k for k, v_ in config.items() for v in v_}
    
    with FS.open(testdatapath) as f:
        data = json.loads(f.read())

    return user2domain, data

def getKey():
    with FS.open(st.secrets['GSHEETKEY']) as f:
        key = json.loads(f.read())
    return key

def challenge():
    user2domain, data_ = load(st.secrets['CONFIGPATH'], st.secrets['TESTDATAPATH'])
    data = copy.deepcopy(data_)
    with st.sidebar.container():
        pwd = st.text_input(label='Enter User ID')
        submitted = st.button("Click to Begin")
    
    if submitted or pwd != '':
        if pwd in user2domain:
            main(pwd, user2domain[pwd], data[user2domain[pwd]])
        else:
            st.error('Wrong password')
            st.stop()

def send(user, relevant, interesting=None):
    package = json.dumps({'relevant':relevant})
    gc = gspread.service_account_from_dict(getKey())
    sh = gc.open_by_key(st.secrets['GSHEET'])
    ws = sh.sheet1
    row_to_update = int(ws.cell(2,1).value)+2
    ws.update_cell(row_to_update,2,user)
    ws.update_cell(row_to_update,3,package)
    st.balloons()
    st.success('Thank you!')

    

def main(user, domain, data):

    _ = random.Random(99).shuffle(data)

    relevant = {}
    interesting = {}

    for d in data:
        relevant[d['index']] = False
        interesting[d['index']] = False

    st.markdown(f'### Recommender Engine Validation Exercise for {domain}')

    styler = 'margin-block-start:0px;margin-block-end:11px; padding-left:20px; width:80%; min-width:400px; max-width: 700px'
    welcome = [
        (f'<p style="{styler}">Welcome! Thank you for taking the time to help us with this experiment.</p>'),
        (f'<p style="{styler}">We have compiled 30 random pieces of news from Atium, some of which were '
        'predicted by our newly developed recommender engine to be of similar to your'
        ' reading preferences.</p>'),
        (f'<p style="{styler}">We would like your help to indicate which are relevant to your work and '
        'which ones seem interesting to you. Kindly use the checkboxes'
        ' to the right to indicate your choices and hit the submit button at the '
        'bottom of the page. You may hit submit multiple times and we will only use '
        'your latest submission.</p>'),
        '<p style="border-bottom: 1px solid grey">Kindly submit by <b>31 Jan 2022</b> please!</p>'
    ]

    with st.container():
        st.markdown(''.join(welcome), unsafe_allow_html=True)

    columns_split = [0.3, 5,0.2,2,0.4]
    with st.form('myform'):
        # st.form_submit_button('Submit',
        #     on_click=onclick, 
        #     kwargs=dict(relevant=relevant, interesting=interesting))

        _, c1, c2, c3, c4 = st.columns(columns_split)
        c1.markdown('##### News Pieces')

        for i, d in enumerate(data):
            with st.container():
                _, a, c, b, _ = st.columns(columns_split)
                a.markdown(f'**{d["title"]}**')
                a.caption(d['content'][:300].replace('\n','. ')+'...')
                relevant[d['index']] = b.radio(label='How relevant is this?', index=2, key=f'C{i}', 
                    options=['Very Relevant!', 'Somewhat Relevant.', 'Somewhat Irrelevant.', 'Very Irrelevant!'])
                b.write('')
                b.write('')
                b.write('')
                b.write('')
                
                
                
        submitted = st.form_submit_button('Submit', on_click=send, kwargs=dict(user=user, relevant=relevant, interesting=None))
    return submitted
if __name__ == '__main__':
    submitted = challenge()
    if submitted:
        st.stop()
