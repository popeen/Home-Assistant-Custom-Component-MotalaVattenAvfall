## Home Assistant addon for Motala Vatten & Avfall

A sensor for getting collection date for garbage and sludge from Motala Vatten & Avfall.
If you have multiple garbage cans in the app you need to set up one sensor for each.

|Parameter| What to put |
|--|--|
| Name | This is the name you want for the sensor in Home Assistant |
| Address | Your home address |
| Type | This is the "type" name you see in the app. You will probably have something similar to the examples |


```
- platform: motalavattenavfall
  name: "Garbage collection date"
  address: "My address"
  type: "Tunna 1"
```
```
- platform: motalavattenavfall
  name: "Garbage collection date"
  address: "My address"
  type: "Hushållsavfall"
```
```  
- platform: motalavattenavfall
  name: "Sludge collection date"
  address: "My address"
  type: "Slam"
```
