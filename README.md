# Tutina: Predict and control indoor temperatures

Tutina (Finnish for *shivering*) is a machine learning model and a home
automation tool for predicting and controlling indoor temperature.

It consists of the following components
 - A web application hosting data storage for past states (weather conditions,
   forecasts, HVAC device states, door and window opening states), and making
   predictions based on a machine learning model
 - A Home Assistant addon interacting with the web application, and producing
   the necessary data for the model.

Currently, only the data collection and model training is in place. In the
future, I want to use the model to answer questions like:
 - If I start heating now, when will the indoor temperature reach the desired
   value?
 - If I stop heating now, how much until the temperature drops below some
   threshold?
 - Can I cool enough by opening windows, or do I need AC?

Tutina does not come with batteries included. You'll need an individual
deployment, and a very specific Home Assistant setup to make it work. Building
an open smart indoor climate system that anyone can use is currently not in
scope of this project.
