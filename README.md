# Hello There! Meet MCDI!
A Python application/library for Minecraft to build redstone musics effortlessly from MIDI or VPR files. 

## Getting started
To run this app, you need:
+ Python 3.8 or newer
  + Package: mido (+ rtmidi-python)
  + Package: pillow (PIL)
  
This app creates music by generating mcfunction(s), so only **Minecraft (Java Edition) 1.13 or newer** are supported. 

## See how cool this thing is!
+ Improved realtime generator
[打上花火](https://www.bilibili.com/video/BV1Hz4y1f7FW) [Lemon](https://www.bilibili.com/video/BV1954y1U7C7)
+ Legacy in-game generator :(
[千本樱](https://www.bilibili.com/video/BV1Hz4y1f7FW)  [恋爱循环](https://www.bilibili.com/video/BV1Na4y1i7tV)

## ~~We even have a GUI!~~ No GUI now :(
~~Run gui_main.py, and then you get a GUI application which is really simple to use!~~

## Frontends
+ WorkerXG: Generates music that is played by the XG resource pack, which is built on YAMAHA XG wavetable and has a better sound quality.
+ Soma: Generates music that is played by the [Soma](https://www.mcbbs.net/thread-709092-1-1.html) resource pack, which is built on Microsoft GS/GM wavetable and has a good sound quality. 
+ Vanilla: Generates music that can be directly played in Minecraft without having any resource pack installed, which has worse sound quality. 
+ MCRG (Beta): Generates music that is played by the resource pack generated by [MCRG](https://github.com/ExMatics/mcrg), which is highly customizable like auto-tune remix.

## Realtime Generator and MIDIout++
~~Forget these frontends!~~ We added a hack to MCDI that allows you to play music directly with MIDI devices ~~and you can throw resource packs into garbage can~~. To run this hack, you need a Minecraft 1.16.x with Fabric and [MIDIOut++](https://github.com/FrankYang6921/midiout-) mod.

## Plugins
+ `lyric.py`
    + Lyric: Lyric generated by .lrc files, useful for video making.
+ `piano.py`
    + Piano: Shows a fancy piano roll with fancy graphics. *Just for fun:)*
+ `title.py`
    + MainTitle: Title at the beginning and the end of the music, useful for video making.
    + CopyTitle: Title throughout the music(e.g. copyright, author), useful for video making.
+ `tweaks.py`
    + Viewport: Fixed or initial viewport for players, useful for video making.
    + PigPort: Fixed or initial viewport riding pigs, useful for video making.
    + ProgressBar: Simply shows a progress bar, useful for video making.
    + FixedTime: Allows you to have a fixed time while playing the music.
    + FixedRain: Allows you to have a fixed rain while playing the music.
    
\[ Still adding more! Just look forward! \]

## Middlewares
\[Nothing here for the time being.\]
