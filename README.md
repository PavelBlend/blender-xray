# blender-xray [![AppVeyor Status](https://img.shields.io/appveyor/build/PavelBlend/blender-xray?logo=AppVeyor&label=AppVeyor)](https://ci.appveyor.com/project/PavelBlend/blender-xray/branch/develop) [![Code Coverage](https://codecov.io/gh/PavelBlend/blender-xray/graph/badge.svg)](https://codecov.io/gh/PavelBlend/blender-xray)
XRay-engine import/export plugin for [blender](http://www.blender.org/).

## Supported formats
| Extension | Description           | Can import | Can export |
|-----------|-----------------------|:----------:|:----------:|
| .object   | Source models         | Yes        | Yes        |
| .anm      | Animation paths       | Yes        | Yes        |
| .dm       | Detail model          | Yes        | Yes        |
| .details  | Level details         | Yes        | Yes        |
| .skl      | Skeletal action       | Yes        | Yes        |
| .skls     | Skeletal actions      | Yes        | Yes        |
| .bones    | Bones data            | Yes        | Yes        |
| .err      | Error list            | Yes        | No         |
| .part     | Scene objects         | Yes        | No         |
| .level    | Scene selection       | Yes        | Yes        |
| level     | Game level            | Yes        | Yes        |
| .ogf      | Compiled models       | Yes        | Yes        |
| .omf      | Game skeletal actions | Yes        | Yes        |

## Installation
Follow [wiki instructions](https://github.com/PavelBlend/blender-xray/wiki/Installation).

## License
Almost all the code is published under the liberal terms of the BSD License, see the [LICENSE](LICENSE) file.
The only exception is the LZHUF module (see special copyrights there).
