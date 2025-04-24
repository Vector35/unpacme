# Unpac.Me Plugin (v1.2)

Author: **Vector 35 Inc**

_Simple plugin to interface Binary Ninja with the UnpacMe automatic unpacking service_

## Description:

This plugin lets you easily submit binaries and download unpacked results from [unpac.me](https://unpac.me/).

You will first need to sign up for a free account before you can use it. The first time you try to upload or download you will be prompted for your API Key which is available from your [account page](https://www.unpac.me/account).

Current features:

- Upload a file to be unpacked. Available from the `Plugins/UnpacMe` menu and command-palette, works on the currently open file.
- Download a previously extracted file. Available from the `Plugins/UnpacMe` menu and command-palette.

![](https://github.com/Vector35/unpacme/blob/master/media/download.png?raw=true)
![](https://github.com/Vector35/unpacme/blob/master/media/menu.png?raw=true)

## Installation Instructions

Use the plugin manager or clone this to your [user plugin folder](https://docs.binary.ninja/getting-started.html#user-folder).

## Minimum Version

This plugin requires the following minimum version of Binary Ninja:

* 3469

## Troubleshooting

If you receive python errors, you may need to upgrade your version of python to support requests with HTTPS support.

## License

This plugin is released under a MIT license.

## Metadata Version

2
