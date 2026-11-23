import tensorflow_data_validation as tfdv
import pandas as pd
class CmfAnalysis():
    def __init__(self):
        pass

    def create_statistics(self,data_path,feature_stats_path):
        statistics=tfdv.generate_statistics_from_csv(data_path)
        tfdv.write_stats_text(statistics, feature_stats_path)

    def visualize_statistics(self,statistics):
        stats=tfdv.load_statistics(statistics)
        tfdv.visualize_statistics(stats)

    def create_schema(self,data_path,schema_path):
        schema=tfdv.infer_schema(statistics=tfdv.generate_statistics_from_csv(data_path,delimiter=";"))
        tfdv.write_schema_text(schema,schema_path)

    def validate_data(self,train_stats_path,eval_path,schema_path):
        new_csv_stats = tfdv.load_statistics(train_stats_path)
        eval_stats=tfdv.load_statistics(eval_path)
        schema=tfdv.load_schema_text(schema_path)
        anomalies = tfdv.validate_statistics(statistics=eval_stats, schema=schema)
        return anomalies

    def display_anomalies(self,anomalies):
        tfdv.display_anomalies(anomalies)

if __name__=="__main__":
    validator=CmfAnalysis()
