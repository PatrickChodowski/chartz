
# ChartZ!

### See everything.

Have you ever run exploratory data analysis before and wondered "Hmmm would be cool to view all the charts at the same time without scrolling or changing tab". 

Well I had for sure and I have good news!  That's exactly why this package was created. ChartZ! is the remedy for all of us who are not able to memorize insights from the chart you have seen 5 seconds ago. 

Solution to our struggles is so obvious - just have all the charts visible at once. Quite simple, right?

Here, have a screenshot to get you excited (I am aware of the fact that UI still looks scuffed):

![view to make you excited](https://github.com/PatrickChodowski/chartz/blob/master/exciting_view.png "Exciting view")


### How it works

Whole package is basically a Flask Blueprint module that can be added to any Flask app. As a first step you have to define data sources (currently only works for big query and postgresql tables). Then you add the tables with definitions for metrics and dimensions fields. Last step is defining dimensional filters and possible values for those filters.

ChartZ! UI will get automatically updated with your settings and you are ready to analyze data! Select your data source, plot type, metric, dimension, aggregation and click on "add plot". New plot will be automatically added to the grid view. I know, thats amazing. Make another plot. It will get added to the view next to the first one. It's so good its unbelievable it's still legal.

Go ahead and save your plots as a view. You will be able to load it later from saved views so you will never have to click-out the same combination of plots EVER AGAIN WOW.

![demo of load view](https://github.com/PatrickChodowski/chartz/blob/master/load_view_demo.gif "Load views")


### Features

 - Connects to BigQuery and Postgresql tables (as of now)
 - Can run on google cloud as app engine
 - Contains 4 basic plot types - bar, scatter, line and table (also a shotchart for NBA data, if you need it, it's there, you are welcome)
 - More plots can be added  
 - Unlimited amount of charts on one page
 - Saving and loading views
 - Plot caching

 
 
### Non features:
 - Although its bootstrap based, I am not taking any responsibility for mobile version (Why would you run your data analysis on mobile you sick bastard)
 - Plot types can't be added without going into package code... yet
 - Handles only 3 aggregation types for now
 
 
### To do list:
 
 - Handling more aggregation, especially percentiles
 - Allowing users to easily add plots (Plot is basically a function that receives data as input and results in HTML object like Bokeh plot)
 - Automatic iteration by category
 - Automatic creation of .yml table descriptions
 - Improve styling/UI
 - Improve JS code (I am not a JS guy at all, I am learning it right now on as I go. If you like this package and you can write nice JS then please reach out. There are jQuery dependencies that I am not able to tackle, help)
 - Handle different operators (I really should have done it before but meh)
 