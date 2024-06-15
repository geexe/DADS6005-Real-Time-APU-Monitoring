#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 Confluent Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# A simple example demonstrating use of AvroDeserializer.

#pip install confluent_kafka
#pip install pandas
#pip install pycaret
#pip install river
#pip install scikit-learn
#pip install fastavro

import argparse
import os

from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from time import sleep
import pandas as pd
from pycaret.regression import load_model, predict_model
from sklearn.metrics import mean_squared_error
import random

from river import linear_model
from river import tree
from river import multiclass
from river import neighbors
from river import naive_bayes
from river import datasets
from river import evaluate
from river import metrics
from river import ensemble
from river import preprocessing


model = tree.HoeffdingTreeClassifier(
        grace_period=100,
    )
model2 = tree.HoeffdingTreeClassifier(
        grace_period=100,
    )
model3 = tree.HoeffdingTreeClassifier(
        grace_period=100,
    )
bal_acc = metrics.BalancedAccuracy()
bal_acc2 = metrics.BalancedAccuracy()
bal_acc3 = metrics.BalancedAccuracy()
saved_model = load_model('model5000')
saved_model2 = load_model('model2')

class User(object):

    # Edit to monitoring data
    def __init__(self, timestamp, TP2,TP3,H1,DV_pressure,Reservoirs,Oil_temperature,Motor_current
                 ,COMP,DV_eletric,Towers,MPG,LPS,Pressure_switch,Oil_level,Caudal_impulses,y):
        self.timestamp = timestamp
        self.TP2 = TP2 
        self.TP3 = TP3
        self.H1 = H1
        self.DV_pressure = DV_pressure
        self.Reservoirs = Reservoirs
        self.Oil_temperature = Oil_temperature
        self.Motor_current = Motor_current
        self.COMP = COMP
        self.DV_eletric = DV_eletric
        self.Towers = Towers
        self.MPG = MPG
        self.LPS = LPS
        self.Pressure_switch = Pressure_switch
        self.Oil_level = Oil_level
        self.Caudal_impulses = Caudal_impulses
        self.y = y

def dict_to_user(obj, ctx):
    """
    Converts object literal(dict) to a User instance.

    Args:
        obj (dict): Object literal(dict)

        ctx (SerializationContext): Metadata pertaining to the serialization
            operation.
    """

    if obj is None:
        return None

    # Edit to monitoring data
    return User(timestamp=obj["timestamp"], TP2=obj["TP2"], TP3= obj["TP3"],
                H1=obj["H1"],DV_pressure=obj["DV_pressure"], Reservoirs=obj["Reservoirs"]
                ,Oil_temperature=obj["Oil_temperature"], Motor_current=obj["Motor_current"]
                ,COMP=obj['COMP'], DV_eletric=obj['DV_eletric'],Towers=obj['Towers']
                ,MPG=obj['MPG'], LPS=obj['LPS'], Pressure_switch=obj['Pressure_switch'],
                Oil_level=obj['Oil_level'],Caudal_impulses=obj['Caudal_impulses'], y=obj["y"])

def main(args):
    topic = args.topic
    is_specific = args.specific == "true"

    if is_specific:
        # Edit to new schema
        schema = "user_specific1.avsc"
    else:
        schema = "user_generic.avsc"

    path = os.path.realpath(os.path.dirname(__file__))
    with open(f"{path}/avro/{schema}") as f:
        schema_str = f.read()

    sr_conf = {'url': args.schema_registry}
    schema_registry_client = SchemaRegistryClient(sr_conf)

    avro_deserializer = AvroDeserializer(schema_registry_client,
                                         schema_str,
                                         dict_to_user)

    consumer_conf = {'bootstrap.servers': args.bootstrap_servers,
                     'group.id': args.group,
                     'auto.offset.reset': "latest"}

    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])



    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            user = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
            # Create a dataframe for the consuming data to feed into the ML model.
            
            data = {'timestamp':user.timestamp, 'TP2':user.TP2,
                    'TP3':user.TP3,'H1':user.H1,
                    'DV_pressure':user.DV_pressure, 'Reservoirs':user.Reservoirs
                    ,'Oil_temperature':user.Oil_temperature, 'Motor_current' : user.Motor_current
                    ,'COMP': user.COMP,'DV_eletric':user.DV_eletric,'Towers' : user.Towers
                    ,'MPG': user.MPG,'LPS':user.LPS, 'Pressure_switch' : user.Pressure_switch
                    ,'Oil_level':user.Oil_level, 'Caudal_impulses':user.Caudal_impulses}
            data2 = {'timstamp':user.timestamp, 'TP2':user.TP2,
                    'TP3':user.TP3,
                    'DV_pressure':user.DV_pressure,
                    'Oil_temperature':user.Oil_temperature, 'Motor_current' : user.Motor_current
                    ,'Towers' : user.Towers
                    ,'LPS':user.LPS, 'Pressure_switch' : user.Pressure_switch
                    ,'Oil_level':user.Oil_level, 'Caudal_impulses':user.Caudal_impulses}
            data3 = {'timstamp':user.timestamp, 'TP2':user.TP2,
                    'TP3':user.TP3,
                    'DV_pressure':user.DV_pressure,
                    'Oil_temperature':user.Oil_temperature, 'Motor_current' : user.Motor_current
                    ,'COMP': user.COMP ,'Towers' : user.Towers
                    ,'LPS':user.LPS, 'Pressure_switch' : user.Pressure_switch
                    ,'Oil_level':user.Oil_level, 'Caudal_impulses':user.Caudal_impulses}
            
            print(data)
            
            # Use offline (Batch) model to predict result from streaming
            # print(type(predictions))
            df = pd.DataFrame(data,index=[user.timestamp])
            predictions = predict_model(saved_model, data=df)
            
            print("Predicted", predictions.iloc[0]['prediction_label']," VS Actual=",user.y)
            print(mean_squared_error([user.y] , [predictions.iloc[0]['prediction_label']] ) )

            df2 = pd.DataFrame(data2,index=[user.timestamp])
            predictions = predict_model(saved_model2, data=df2)
            
            print("Predicted", predictions.iloc[0]['prediction_label']," VS Actual=",user.y)
            print(mean_squared_error([user.y] , [predictions.iloc[0]['prediction_label']] ) )

            # Online (Real-time) model to predict result from streaming
            y_pred = model.predict_one(data)
            y_prob = model.predict_proba_one(data)
            model.learn_one(data, user.y)
            print("y_pred = ",y_pred)
            print("y_prob = ",y_prob)
            bal_acc.update(user.y, y_pred)
            print(bal_acc)
            
            y_pred2 = model2.predict_one(data2)
            y_prob2 = model2.predict_proba_one(data2)
            model2.learn_one(data2, user.y)
            print("y_pred2 = ",y_pred2)
            print("y_prob2 = ",y_prob2)
            bal_acc2.update(user.y, y_pred2)
            print(bal_acc2)

            try:
                predicted = [y_pred, y_pred2]
                weight = [bal_acc.get(), bal_acc2.get()]
                total_weight = sum(weight)
                prob = []
                for i in range(len(weight)):
                    if(total_weight == 0):
                        prob.append(0)
                    else:
                        prob.append(weight[i]/total_weight)
                chosen_element = random.choices(predicted, weights=prob, k=1)[0]
                print("Chosen:", chosen_element)
            except:
                continue
            

            '''y_pred3 = model3.predict_one(data3)
            y_prob3 = model3.predict_proba_one(data3)
            model3.learn_one(data3, user.y)
            print("y_pred3 = ",y_pred3)
            print("y_prob3 = ",y_prob3)
            bal_acc3.update(user.y, y_pred3)
            print("Balanced Accuracy: ", bal_acc3)'''

        except KeyboardInterrupt:
            break

        sleep(1)

    consumer.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AvroDeserializer example")
    parser.add_argument('-b', dest="bootstrap_servers", required=True,
                        help="Bootstrap broker(s) (host[:port])")
    parser.add_argument('-s', dest="schema_registry", required=True,
                        help="Schema Registry (http(s)://host[:port]")
    parser.add_argument('-t', dest="topic", default="example_serde_avro",
                        help="Topic name")
    parser.add_argument('-g', dest="group", default="example_serde_avro",
                        help="Consumer group")
    parser.add_argument('-p', dest="specific", default="true",
                        help="Avro specific record")

    main(parser.parse_args())

# Example
# python avro_monitor_consumer.py -b "localhost:9092" -s "http://localhost:8081" -t "raw2"