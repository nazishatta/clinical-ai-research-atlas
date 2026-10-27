from pathlib import Path
from streamlit.testing.v1 import AppTest
APP=Path(__file__).resolve().parents[1]/'app.py'

def test_app_filters_reset_and_network_controls():
 app=AppTest.from_file(str(APP),default_timeout=90).run()
 assert not app.exception
 assert len(app.tabs)==5
 app.slider(key='years').set_range(2020,2023).run()
 assert not app.exception
 app.multiselect(key='signals').select('Calibration').run()
 assert not app.exception
 app.selectbox(key='topic').select(app.selectbox(key='topic').options[1]).run()
 assert not app.exception
 app.slider(key='shared').set_value(5).run()
 assert not app.exception
 app.button[0].click().run()
 assert not app.exception
 assert app.slider(key='years').value==(2016,2025)
 assert app.multiselect(key='signals').value==[]

def test_empty_subset_does_not_crash():
 app=AppTest.from_file(str(APP),default_timeout=90).run()
 app.slider(key='years').set_range(2016,2016).run()
 app.multiselect(key='signals').select('Calibration').run()
 app.selectbox(key='topic').select(app.selectbox(key='topic').options[-1]).run()
 assert not app.exception
 assert app.metric[0].value=='0'

def test_topic_mix_chart_and_text_alternatives_render():
 app=AppTest.from_file(str(APP),default_timeout=90).run()
 assert not app.exception
 texts=[m.value for m in app.markdown]
 assert any('How the topic mix changed over time' in t for t in texts)
 assert sum(t.startswith('**In short:**') for t in texts)>=4
 assert any('#### Accessibility' in t for t in texts)
 app.selectbox(key='topic').select(app.selectbox(key='topic').options[1]).run()
 assert not app.exception
 assert any('needs at least two topics' in i.value for i in app.info)
