## Home Assistant addon for Motala Vatten & Avfall

[![GitHub Release][releases-shield]][releases]
![Project Stage][project-stage-shield]
[![issues-shield]](issues)
[![License][license-shield]](LICENSE.md)
[![Buy me a coffee][buymeacoffee-shield]][buymeacoffee]

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
[releases-shield]: https://img.shields.io/github/release/popeen/Home-Assistant-Addon-MotalaVattenAvfall.svg
[releases]: https://github.com/popeen/Home-Assistant-Addon-MotalaVattenAvfall/releases
[project-stage-shield]: https://img.shields.io/badge/project%20stage-ready%20for%20use-green.svg
[issues-shield]: https://img.shields.io/github/issues-raw/popeen/Home-Assistant-Addon-MotalaVattenAvfall.svg
[license-shield]: https://img.shields.io/github/license/popeen/Home-Assistant-Addon-MotalaVattenAvfall.svg
[buymeacoffee-shield]: https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-2.svg
[buymeacoffee]: https://www.buymeacoffee.com/popeen
