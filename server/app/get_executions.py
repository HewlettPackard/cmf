from cmflib import cmfquery
import pandas as pd

def index(mlmdfilepath):
   #template = loader.get_template('index/table.html') # getting our template
   #return HttpResponse(template.render())
   query = cmfquery.CmfQuery(mlmdfilepath)
   names = query.get_pipeline_names()
   for name in names:
        stages = query.get_pipeline_stages(name)
        df = pd.DataFrame()
        for stage in stages:
            executions = query.get_all_executions_in_stage(stage)
            df = pd.concat([df, executions], sort=True, ignore_index=True)
            # df = df.to_html(classes='mystyle')
        print(df)
        return df
