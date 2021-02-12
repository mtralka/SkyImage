# SkyImage

This project and documentation is a work in progress and is thus subject to unexpected change.

Please check out the [Interaction Documentation](https://mtralka.github.io/SkyImage/)

## Quick Start Guide

### Requirements

This project uses [Conda](https://docs.conda.io/en/latest/). Please install the `requirements.txt` with the command:

```
    conda create --name <env> --file requirements.txt
```

### Setting Stations

`SkyImage` reads possible stations through a `stations.json` file in the root project directory. The structure is as follows

```
    {
        $STATION_NAME: {
         "lat" : $LAT,
         "lon" : $LON
        },
        ...
    }
```

#### Where

- `$STATION_NAME` is the searcable station name callable through the `station` kwarg in the main `SkyImage` object.

- `$LAT` and `$LON` are used as the coordinates for poi extraction from MODIS imagery and for all subsequent ground imagery processing 

#### Example

```
    {
        "SKYCAM1: {
         "lat" : 38.99,
         "lon" : -76.85
        }
    }
```

## `SkyImage` Object

The `SkyImage` object serves as the main entrypoint for all SkyImage functionality. It handles data-handling and processing automatically. Under the hood, `SkyImage` constructs subsystem station objects - `Sky` and `Ground` - referring to the point-of-origin of the resulting station imagery. These sub-objects can be called independetly, this will be discussed in-depth later

### Usage

|**KWARGS**|  **Meaning** | **Example Usage** |
|---|---|---|
|`year`| (int) year of dataset aquistion| `=2020` |
|`j_day`| (int or str) target Julian day(s) | `=92` or `="92"` or `="92-95"` |
|`station`| (str) target station | `="SKYCAM1"` |
|`modis_path`| (str) rel / abs file path to MODIS data root dir| `="path\\to\\MODIS\\root` |
|`ground_path`|  (str) rel / abs file path to ground data root dir| `="path\\to\\ground\\root` |
|`save_images`|  (bool) save photo and cloud mask results | `="path\\to\\ground\\root` |
|`show_images`|  (bool) show photo and cloud mask results | `="path\\to\\ground\\root` |

```
        import skyimage

        modis_path = "path/to/modis/data"
        ground_path = "path/to/ground/data"

        si = skyimage.SkyImage(
            year=2020, j_day="92", station="SKYCAM1",modis_path=modis_path, ground_path=ground_path)
```

Run `Sky` and `Ground` sub-objects

`si.run()`

Graph results manually

`si.Ground.show_graph(poi=si.Ground.raw_poi["2020092"])`

View consolidated results

`si.results(as_dataframe=True)`

### `Sky` results and properties

````
        sky = si.Sky
        print(sky)
        sky.results(as_dataframe=True)

````

Main `Sky` Properties

|||
|---|---|
|`sky.scenes`|all matched MODIS scenes|
|`sky.scenes_sublayers` | all matched MODIS sublayers |
|`sky.scenes_metadata` | all scene metadata |
|`sky.raw_poi` | all scene's raw extracted poi data |
|`sky.poi`|all scene's processed poi data|

## Independent `Sky` Object Usage

```
        from skyimage.stations.Sky import Sky

        modis_path = "path/to/modis/data"
        sky = Sky(j_day="92-121", year=2020, path=modis_path, station="SKYCAM1" )

        sky.results(as_dataframe=True)

```

## Independent `Ground` Object Usage

```
        from skyimage.stations.Ground import Ground

        ground_path = "path/to/ground/data"

        ground = Ground(j_day="92-94", year=2020, path=ground_path, station="SKYCAM1" )

        ground.results(as_dataframe=True)
```