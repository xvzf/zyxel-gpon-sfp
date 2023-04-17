# "Hacking" the (Telekom) Zyxel GPON SFP module (PMG3000-D20B)
> The SFP can be sourced very easily and is widely available in Germany.

## I just want fiber internet on my non-Telekom router

[jaseg](https://github.com/jaseg/) has written a guide on this [on his blog](https://jaseg.de/blog/telekom-gpon-sfp/).

## TLDR

Checkout the three options for configuring your SFP.
When requiring a serial number change, this can be performed by the CLI only. Note, that some SFP NICs don't support hardwireing the speed settings. In this case, you need to connect the GPON fibre link to the module to be able to access it (see https://github.com/xvzf/zyxel-gpon-sfp/issues/8).

### 1. WEB UI
1. Configure the ethernet interface the SFP is in with the IP `10.10.1.2/24`.
2. Port-forward the SFPs web interface to your local machine via SSH: `ssh -L 127.0.0.1:8080:10.10.1.1:80 <user@router>`.
3. Access the web-interface on `http://localhost:8080`, username `admin`, password `1234`.

### 2. CLI (on the SFP)
> Note: The PLOAM ID has to be HEX encoded, in case yours is a 10-character string, you can transform it using `python3 -c 'print(hex("<enter PLOAM/SLID between the qotes>"))'`. Omit the `0x` prefix.

1. Configure the ethernet interface the SFP is in with the IP `10.10.1.2/24`.
2. SSH into the module using `admin@10.10.1.1`, password `admin`.
3. Login into the CLI with user `admin`, paddword `1234`.
4. Change the _PLOAM/SLID/Installationskennung_ by entering following commands followed by a newline:
    - `hal`
    - `password <PLOAM/SLID>`
5. _Optional_: CHange the serial number using `sn ...`; the first four characters are ASCII encoded, e.g. `SCOM`, the rest is followed in hex.

### 3. CLI (remote)
> Note: requires Python >= 3.8

```
NAME
    zyxel_gpon_sfp.py --sfp_addr=http://10.10.1.1

SYNOPSIS
    zyxel_gpon_sfp.py --sfp_addr=http://10.10.1.1 - COMMAND

COMMANDS
    COMMAND is one of the following:

     info

     set_slid

     set_sn
```


## Motivation
My ISPs ([Deutsche Telekom](https://www.telekom.de/)) FTTH offering uses on a GPON network and distributes ONUs with a 1G (or 2.5G Ethernet) for non-business customers.
I intended to run the fiber directly into my Linux router (using one of the SFP+ ports).
Looking at the business offerings building upon the same technology revealed SFPs distributed only business customers using the [_Digitalisierungsbox Premium 2_](https://www.telekom.de/hilfe/geraete-zubehoer/router/digitalisierungsbox/premium-2#e_745060). 
The mentioned SFP is made by Zyxel with the identifier `PMG3000-D20B` and sold as [_Digitalisierungsbox Glasfaser Modem_](https://geschaeftskunden.telekom.de/internet-dsl/produkt/digitalisierungsbox-glasfasermodem-kaufen) (Telekom only sells it to business customers but it is available online for ~40 Euros).

The module is based on a Lantiq 98035 SoC, [datasheet](https://www.electronicsdatasheets.com/download/51c42036e34e246e4900009c.pdf?format=pdf), [link to OpenWRT forums discussion on Huawei SFP module based on the same SoC](https://forum.openwrt.org/t/support-ma5671a-sfp-gpon/48042).

## Accessing the module

After _reverse engineering_ (this time it has been a `fzf` through all files, not analysing the binaries) the firmware of _Telekom Digitalisierungsbox 2_, I've identified the IP address of the module being `10.10.1.1/24` based on a SQL statement with a comment:
```sql
-- BS-6456: remove marker 'RESERVED' from static IP used to access the SFP module
UPDATE Ip SET Name="" WHERE IpAddress="10.10.1.2" AND Interface="eth1" AND LogicalInterface="eth1";
```

Digging a bit further in plaintext SQL statements reveals the credentials.
```sql
-- ...
INSERT INTO SshConfiguration VALUES ( 1, 0, 5, 22, 'Access only for authorized persons!', 0, '' );
INSERT INTO SshUser VALUES ( 1, 0, 'admin', 'admin', 0 );
-- ...
INSERT INTO GPONConfig VALUES ( 1, 1, '10.10.1.1', 'admin', '1234', '', '' );
```

Well, let's give it a try. SSH access sounds like a charm and is confirmed by nmap:
```bash
xvzf@e300 ~ % nmap 10.10.1.1
Starting Nmap 7.80 ( https://nmap.org ) at 2022-02-02 06:31 UTC
Nmap scan report for 10.10.1.1
Host is up (0.00079s latency).
Not shown: 998 closed ports
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
MAC Address: <redacted> (Zyxel Communications)

Nmap done: 1 IP address (1 host up) scanned in 4.15 seconds
```

Let's give it a try with `ssh admin@10.10.1.1`:
```
#######################################################
#                                                     #
# Please login to CLI mode. Then You can do commands. #
#                                                     #
#######################################################

Entering character mode
Escape character is '^]'.


Login: admin
Password: <not echoed `1234`>
ZYXEL#
ZYXEL# <not echoed `?`>
  linuxshell  Enter linux shell
  show        show
  system
  manufactory
  config
  mib
  sf
  log
  timer
  bsp
  hal
  igmp
  omci
  ssp
ZYXEL# show version
Project Name:              TW2362H-CDEL
Client Product Name:       GTO100I_SFP_ZYXEL
Internal Product Name:     GTO100I_SFP_ZYXEL
Hardware Version:          PMG3000-D20B
Boot Version:              V1.0.0
Client Software Version:   V1.0.0
Internal Software Version: V1.0.0
Build User:                jiangyuanqi
Build Time:                2021-05-08 11:28:36
Build Method:              export ONU=gto100i_sfp_zyxel && cd ../drv && make install && cd .. && make rootfs && make install
GIT Info:                  TW2362H-CDEL_lantiq98035/customize/TW2362H-CDEL_lantiq98035_general_20150131:e057bd83
ZYXEL#
```

So, we can get a linux shell, nice. My SFP is running a (very old) release of [OpenWrt](https://openwrt.org):
```bash
ZYXEL# linuxshell
BusyBox v1.19.4 (2014-06-30 12:00:02 CST) built-in shell (ash)
Enter 'help' for a list of built-in commands.

  _______                     ________        __
 |       |.-----.-----.-----.|  |  |  |.----.|  |_
 |   -   ||  _  |  -__|     ||  |  |  ||   _||   _|
 |_______||   __|_____|__|__||________||__|  |____|
          |__| W I R E L E S S   F R E E D O M
 -----------------------------------------------------
 ATTITUDE ADJUSTMENT (Attitude Adjustment, 12.09_ltq)
 -----------------------------------------------------
  * 1/4 oz Vodka      Pour all ingredients into mixing
  * 1/4 oz Gin        tin with ice, strain into glass.
  * 1/4 oz Amaretto
  * 1/4 oz Triple sec
  * 1/4 oz Peach schnapps
  * 1/4 oz Sour mix
  * 1 splash Cranberry juice
 -----------------------------------------------------
admin@SFP:~# uname -a
Linux SFP 3.10.12 #2 Wed Jul 12 12:01:33 CST 2017 mips GNU/Linux
admin@SFP:~#
```

## Changing GPON Serial Number / PLOAM Password

```
ZYXEL# hal
Hal#
  linuxshell  Enter linux shell
  show        show HAL configuration
  sn          change ont parameters
  password    change ont password
  set         set ont parameters
  to1         change ont to1 interval
  to2         change ont to2 interval
  berinterval change BER interval
  sfthreshold change SF threshold
  sdthreshold change SD threshold
  tcont       add tcont
  no          delete HAL item
  gemport     add HAL item
  reset       Reset all pon configurations
  get         get
  omci        omci
  stream      stream
  mvlanaction mvlanaction
  uni         PPTP UNI configuration
  mtu         MTU R/W
  multicast   multicast configartion
  iphost      iphost
  init        init
  deny        deny
  permit      permit
  monitor     monitor
  mac         mac
  storm       storm
  print       print
  igmp        igmp
  mcastfilt   McastFilt
Hal# sn
  <string> change ont serial number
Hal# password
  <string> Formate:XXXXXXXXXXXXXXXXXXXX
```
The password seems to consist of 10 bytes, entered hex encoded. This is likely the PLOAM password / SLID / _Installationskennung_ / whatever you'd like to call it. 
The `sn` seems to change the serial number of the ONU (ONT) itself. This works, though it expects the first 4 characters to be ASCII encoded (e.g. for the Telekom Glasfasermodem 2, it likely starts with SCOM (hex:`5343 4f4d`)

I assumed the CLI is using the configuration interface of OpenWRT under the hood; turns out I was right:
```
uci show gpon
gpon.ploam=gpon
gpon.ploam.nPassword=0x20 0x20 0x20 0x20 0x20 0x20 0x20 0x20 0x20 0x20
gpon.ploam.nT01=16000
gpon.ploam.nT02=100
gpon.ploam.nEmergencyStopState=0
gpon.ploam.nRogueMsgIdUpstreamReset=255
gpon.ploam.nRogueMsgRepeatUpstreamReset=3
gpon.ploam.nRogueMsgIdDeviceReset=255
gpon.ploam.nRogueMsgRepeatDeviceReset=3
gpon.ploam.nRogueEnable=0
gpon.gtc=gpon
gpon.gtc.bDlosEnable=0
gpon.gtc.bDlosInversion=0
gpon.gtc.nDlosWindowSize=0
gpon.gtc.nDlosTriggerThreshold=0
gpon.gtc.ePower=0
gpon.gtc.nLaserGap=0
gpon.gtc.nLaserOffset=0
gpon.gtc.nLaserEnEndExt=0
gpon.gtc.nLaserEnStartExt=0
gpon.gtc.nDyingGaspHyst=0
gpon.gtc.nDyingGaspMsg=0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00
gpon.gtc.nDyingGaspEnable=0
gpon.ethernet=gpon
gpon.ethernet.bUNI_PortEnable0=1
gpon.ethernet.bUNI_PortEnable1=1
gpon.ethernet.bUNI_PortEnable2=1
gpon.ethernet.bUNI_PortEnable3=1
gpon.gpe=gpon
gpon.gpe.nPeNumber=6
```

## Observing the GPON SN and Password in real time.

### Serial and Password
The `onu` command helps debugging the system:
- `onu gtcpg`: Retrieve password
- `onu gtcsng`: Retrieve serial number

### Connection state
**Connected** (`curr_state=5`)
```bash
admin@SFP:~# onu ploamsg
errorcode=0 curr_state=5
```

**Disconnected** (`curr_state=1`):
```bash
admin@SFP:~# onu ploamsg
errorcode=0 curr_state=1 previous_state=0 elapsed_msec=16907701
```

## Enable 2.5G
2.5G may not be enabled by default on the SFP. Use the following command to enable 2.5 manually:
```
ZYXEL# hal
Hal# set speed 2.5g mode full
```

You may have to disable auto-negotation and set a fixed port speed of 2.5G on your network adapter to make it work.

## HTTP API

Only after getting SSH access I discovered the SFP comes with a WebUI and a _sort of_ API. The CLI `zyxel_gpon_sfp.py` makes use of this API to remotely configure the PLOAM password and possibly SN (again, didn't check it).

## TODO 
- [ ] Prometheus exporter
- [ ] Integrate into OpenWRT
