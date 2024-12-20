# Tutina

Tutina (Finnish for *shivering*) is a home automation tool for predicting and
controlling indoor temperature.

Tutina consists of three components
 - `tutina-ai`, a machine learning model to predict indoor temperature
 - `tutina-app`, a webapp serving the predictions
 - `tutina-ha`, a Home Assistant addon to interact with the model

Currently it's only collecting data and I've started developing the model. In
the future, I want to use the model to answer questions like:
 - If I start heating now, when will the indoor temperature reach the desired value?
 - If I stop heating now, how much until the temperature drops below some threshold?
 - Can I cool enough by opening windows, or do I need AC?

Tutina does not come with batteries included. You'll need a very specific Home
Assistant setup to make it work. Building an open smart indoor climate system
that anyone can use is currently not in scope of this project.
