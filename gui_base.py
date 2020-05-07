# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.html

###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"MCDI GUI 应用程序", pos = wx.DefaultPosition, size = wx.Size( 480,448 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( -1,-1 ), wx.Size( -1,-1 ) )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MainContainer = wx.BoxSizer( wx.VERTICAL )

		self.MIDIPages = wx.Listbook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LB_DEFAULT )
		self.MIDIPageFile = wx.ScrolledWindow( self.MIDIPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
		self.MIDIPageFile.SetScrollRate( 5, 5 )
		self.MIDIPageFile.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPageFileContainer = wx.BoxSizer( wx.VERTICAL )

		MIDIPageFile1 = wx.FlexGridSizer( 0, 2, 0, 0 )
		MIDIPageFile1.SetFlexibleDirection( wx.BOTH )
		MIDIPageFile1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.MIDIPathPrompt = wx.StaticText( self.MIDIPageFile, wx.ID_ANY, u"MIDI文件 路径：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.MIDIPathPrompt.Wrap( -1 )

		MIDIPageFile1.Add( self.MIDIPathPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.MIDIPathPicker = wx.FilePickerCtrl( self.MIDIPageFile, wx.ID_ANY, wx.EmptyString, u"选择一个MIDI文件", u"*.mid", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		MIDIPageFile1.Add( self.MIDIPathPicker, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		MIDIPageFileContainer.Add( MIDIPageFile1, 0, wx.EXPAND, 5 )

		MIDIPageFile2 = wx.FlexGridSizer( 0, 2, 0, 0 )
		MIDIPageFile2.SetFlexibleDirection( wx.BOTH )
		MIDIPageFile2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.DotMCPathPrompt = wx.StaticText( self.MIDIPageFile, wx.ID_ANY, u".minecraft 目录：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.DotMCPathPrompt.Wrap( -1 )

		MIDIPageFile2.Add( self.DotMCPathPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.DotMCPathPicker = wx.DirPickerCtrl( self.MIDIPageFile, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.Size( -1,-1 ), wx.DIRP_DEFAULT_STYLE )
		self.DotMCPathPicker.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

		MIDIPageFile2.Add( self.DotMCPathPicker, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		MIDIPageFileContainer.Add( MIDIPageFile2, 0, wx.EXPAND, 5 )

		MIDIPageFile3 = wx.FlexGridSizer( 0, 3, 0, 0 )
		MIDIPageFile3.SetFlexibleDirection( wx.BOTH )
		MIDIPageFile3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.MCVersionPrompt = wx.StaticText( self.MIDIPageFile, wx.ID_ANY, u"Minecraft 版本：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.MCVersionPrompt.Wrap( -1 )

		MIDIPageFile3.Add( self.MCVersionPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		MCVersionPickerChoices = []
		self.MCVersionPicker = wx.Choice( self.MIDIPageFile, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, MCVersionPickerChoices, 0 )
		self.MCVersionPicker.SetSelection( 0 )
		MIDIPageFile3.Add( self.MCVersionPicker, 0, wx.ALL, 5 )

		self.MCVersionShowOld = wx.CheckBox( self.MIDIPageFile, wx.ID_ANY, u"显示旧版本", wx.DefaultPosition, wx.DefaultSize, 0 )
		MIDIPageFile3.Add( self.MCVersionShowOld, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		MIDIPageFileContainer.Add( MIDIPageFile3, 0, wx.EXPAND, 5 )

		MIDIPageFile4 = wx.FlexGridSizer( 0, 3, 0, 0 )
		MIDIPageFile4.SetFlexibleDirection( wx.BOTH )
		MIDIPageFile4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.MCWorldPrompt = wx.StaticText( self.MIDIPageFile, wx.ID_ANY, u"存档 名称：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.MCWorldPrompt.Wrap( -1 )

		MIDIPageFile4.Add( self.MCWorldPrompt, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 )

		MCWorldPickerChoices = []
		self.MCWorldPicker = wx.Choice( self.MIDIPageFile, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, MCWorldPickerChoices, 0 )
		self.MCWorldPicker.SetSelection( 0 )
		MIDIPageFile4.Add( self.MCWorldPicker, 0, wx.ALL, 5 )

		self.MCVersionDependent = wx.CheckBox( self.MIDIPageFile, wx.ID_ANY, u"禁用版本独立", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.MCVersionDependent.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPageFile4.Add( self.MCVersionDependent, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		MIDIPageFileContainer.Add( MIDIPageFile4, 0, 0, 5 )

		MIDIPageFileAdvance = wx.StaticBoxSizer( wx.StaticBox( self.MIDIPageFile, wx.ID_ANY, u"高级选项" ), wx.VERTICAL )

		MIDIPageFile5 = wx.FlexGridSizer( 2, 3, 0, 0 )
		MIDIPageFile5.SetFlexibleDirection( wx.BOTH )
		MIDIPageFile5.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.PackNamespacePrompt = wx.StaticText( MIDIPageFileAdvance.GetStaticBox(), wx.ID_ANY, u"命名空间：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.PackNamespacePrompt.Wrap( -1 )

		MIDIPageFile5.Add( self.PackNamespacePrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.PackNamespaceInput = wx.TextCtrl( MIDIPageFileAdvance.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		MIDIPageFile5.Add( self.PackNamespaceInput, 0, wx.ALL, 5 )

		self.PackNamespaceAuto = wx.CheckBox( MIDIPageFileAdvance.GetStaticBox(), wx.ID_ANY, u"自动设定", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.PackNamespaceAuto.SetValue(True)
		MIDIPageFile5.Add( self.PackNamespaceAuto, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.PackIdentifierPrompt = wx.StaticText( MIDIPageFileAdvance.GetStaticBox(), wx.ID_ANY, u"包名称：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.PackIdentifierPrompt.Wrap( -1 )

		MIDIPageFile5.Add( self.PackIdentifierPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.PackIdentifierInput = wx.TextCtrl( MIDIPageFileAdvance.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		MIDIPageFile5.Add( self.PackIdentifierInput, 0, wx.ALL, 5 )

		self.PackIdentifierAuto = wx.CheckBox( MIDIPageFileAdvance.GetStaticBox(), wx.ID_ANY, u"自动设定", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.PackIdentifierAuto.SetValue(True)
		MIDIPageFile5.Add( self.PackIdentifierAuto, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		MIDIPageFileAdvance.Add( MIDIPageFile5, 1, wx.EXPAND, 5 )


		MIDIPageFileContainer.Add( MIDIPageFileAdvance, 0, wx.EXPAND, 5 )


		self.MIDIPageFile.SetSizer( MIDIPageFileContainer )
		self.MIDIPageFile.Layout()
		MIDIPageFileContainer.Fit( self.MIDIPageFile )
		self.MIDIPages.AddPage( self.MIDIPageFile, u"文件与生成", False )
		self.MIDIPageTiming = wx.ScrolledWindow( self.MIDIPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
		self.MIDIPageTiming.SetScrollRate( 5, 5 )
		self.MIDIPageTiming.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPageTimingContainer = wx.BoxSizer( wx.VERTICAL )

		self.MIDIPageTimingPages = wx.Choicebook( self.MIDIPageTiming, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.CHB_DEFAULT )
		self.TimingFlex = wx.Panel( self.MIDIPageTimingPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		MIDIPageTiming1 = wx.FlexGridSizer( 0, 2, 0, 0 )
		MIDIPageTiming1.SetFlexibleDirection( wx.BOTH )
		MIDIPageTiming1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.FlexDurationPrompt = wx.StaticText( self.TimingFlex, wx.ID_ANY, u"时长（自动=0，秒）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.FlexDurationPrompt.Wrap( -1 )

		MIDIPageTiming1.Add( self.FlexDurationPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.FlexDurationSpin = wx.SpinCtrlDouble( self.TimingFlex, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 65535, 0, 0.5 )
		self.FlexDurationSpin.SetDigits( 0 )
		MIDIPageTiming1.Add( self.FlexDurationSpin, 0, wx.ALL, 5 )

		self.FlexTolerancePrompt = wx.StaticText( self.TimingFlex, wx.ID_ANY, u"容差（正负秒）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.FlexTolerancePrompt.Wrap( -1 )

		MIDIPageTiming1.Add( self.FlexTolerancePrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.FlexToleranceSpin = wx.SpinCtrlDouble( self.TimingFlex, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0.1, 127, 3, 0.1 )
		self.FlexToleranceSpin.SetDigits( 0 )
		MIDIPageTiming1.Add( self.FlexToleranceSpin, 0, wx.ALL, 5 )

		self.FlexSteppingPrompt = wx.StaticText( self.TimingFlex, wx.ID_ANY, u"步进（秒，过大无效）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.FlexSteppingPrompt.Wrap( -1 )

		MIDIPageTiming1.Add( self.FlexSteppingPrompt, 0, wx.ALL, 5 )

		self.FlexSteppingSpin = wx.SpinCtrlDouble( self.TimingFlex, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0.01, 1, 0.100000, 0.01 )
		self.FlexSteppingSpin.SetDigits( 0 )
		MIDIPageTiming1.Add( self.FlexSteppingSpin, 0, wx.ALL, 5 )


		self.TimingFlex.SetSizer( MIDIPageTiming1 )
		self.TimingFlex.Layout()
		MIDIPageTiming1.Fit( self.TimingFlex )
		self.MIDIPageTimingPages.AddPage( self.TimingFlex, u"弹性时长（推荐）", True )
		self.TimingStaticT = wx.Panel( self.MIDIPageTimingPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		MIDIPageTiming2 = wx.FlexGridSizer( 0, 2, 0, 0 )
		MIDIPageTiming2.SetFlexibleDirection( wx.BOTH )
		MIDIPageTiming2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.StaticTickRatePrompt = wx.StaticText( self.TimingStaticT, wx.ID_ANY, u"刻速率（1/x）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.StaticTickRatePrompt.Wrap( -1 )

		MIDIPageTiming2.Add( self.StaticTickRatePrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.StaticTickRateSpin = wx.SpinCtrlDouble( self.TimingStaticT, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 1, 65535, 50, 0.1 )
		self.StaticTickRateSpin.SetDigits( 0 )
		MIDIPageTiming2.Add( self.StaticTickRateSpin, 0, wx.ALL, 5 )


		self.TimingStaticT.SetSizer( MIDIPageTiming2 )
		self.TimingStaticT.Layout()
		MIDIPageTiming2.Fit( self.TimingStaticT )
		self.MIDIPageTimingPages.AddPage( self.TimingStaticT, u"固定刻速率", False )
		self.TimingStaticD = wx.Panel( self.MIDIPageTimingPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		MIDIPageTiming3 = wx.FlexGridSizer( 0, 2, 0, 0 )
		MIDIPageTiming3.SetFlexibleDirection( wx.BOTH )
		MIDIPageTiming3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.StaticDurationPrompt = wx.StaticText( self.TimingStaticD, wx.ID_ANY, u"时长（自动=0，秒）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.StaticDurationPrompt.Wrap( -1 )

		MIDIPageTiming3.Add( self.StaticDurationPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.StaticDurationSpin = wx.SpinCtrlDouble( self.TimingStaticD, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 65535, 0.000000, 0.5 )
		self.StaticDurationSpin.SetDigits( 0 )
		MIDIPageTiming3.Add( self.StaticDurationSpin, 0, wx.ALL, 5 )


		self.TimingStaticD.SetSizer( MIDIPageTiming3 )
		self.TimingStaticD.Layout()
		MIDIPageTiming3.Fit( self.TimingStaticD )
		self.MIDIPageTimingPages.AddPage( self.TimingStaticD, u"固定时长", False )
		MIDIPageTimingContainer.Add( self.MIDIPageTimingPages, 1, wx.EXPAND |wx.ALL, 5 )


		self.MIDIPageTiming.SetSizer( MIDIPageTimingContainer )
		self.MIDIPageTiming.Layout()
		MIDIPageTimingContainer.Fit( self.MIDIPageTiming )
		self.MIDIPages.AddPage( self.MIDIPageTiming, u"时序", False )
		self.MIDIPageEffect = wx.Panel( self.MIDIPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.MIDIPageEffect.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPageEffectContainer = wx.BoxSizer( wx.VERTICAL )

		MIDIPageEffect1 = wx.FlexGridSizer( 0, 3, 0, 0 )
		MIDIPageEffect1.SetFlexibleDirection( wx.BOTH )
		MIDIPageEffect1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.EffectAllowPan = wx.CheckBox( self.MIDIPageEffect, wx.ID_ANY, u"允许立体声像", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.EffectAllowPan.SetValue(True)
		MIDIPageEffect1.Add( self.EffectAllowPan, 0, wx.ALL, 5 )

		self.EffectAllowGVol = wx.CheckBox( self.MIDIPageEffect, wx.ID_ANY, u"允许全局音量", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.EffectAllowGVol.SetValue(True)
		MIDIPageEffect1.Add( self.EffectAllowGVol, 0, wx.ALL, 5 )

		self.EffectAllowPitch = wx.CheckBox( self.MIDIPageEffect, wx.ID_ANY, u"允许弯音轮", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.EffectAllowPitch.SetValue(True)
		MIDIPageEffect1.Add( self.EffectAllowPitch, 0, wx.ALL, 5 )


		MIDIPageEffectContainer.Add( MIDIPageEffect1, 0, wx.EXPAND, 5 )

		MIDIPageEffect2 = wx.FlexGridSizer( 0, 2, 0, 0 )
		MIDIPageEffect2.SetFlexibleDirection( wx.BOTH )
		MIDIPageEffect2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.EffectPitchFactorPrompt = wx.StaticText( self.MIDIPageEffect, wx.ID_ANY, u"弯音系数（倍率）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.EffectPitchFactorPrompt.Wrap( -1 )

		MIDIPageEffect2.Add( self.EffectPitchFactorPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.EffectPitchFactorSpin = wx.SpinCtrlDouble( self.MIDIPageEffect, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1, 1.000000, 0.01 )
		self.EffectPitchFactorSpin.SetDigits( 0 )
		MIDIPageEffect2.Add( self.EffectPitchFactorSpin, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.EffectVolumeFactorPrompt = wx.StaticText( self.MIDIPageEffect, wx.ID_ANY, u"音量系数（倍率）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.EffectVolumeFactorPrompt.Wrap( -1 )

		MIDIPageEffect2.Add( self.EffectVolumeFactorPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.EffectVolumeFactorSpin = wx.SpinCtrlDouble( self.MIDIPageEffect, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0.1, 5, 1.000000, 0.1 )
		self.EffectVolumeFactorSpin.SetDigits( 0 )
		MIDIPageEffect2.Add( self.EffectVolumeFactorSpin, 0, wx.ALL, 5 )


		MIDIPageEffectContainer.Add( MIDIPageEffect2, 0, wx.EXPAND, 5 )

		MIDIPageEffect3 = wx.FlexGridSizer( 0, 3, 0, 0 )
		MIDIPageEffect3.SetFlexibleDirection( wx.BOTH )
		MIDIPageEffect3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.EffectDoLongAnalysis = wx.CheckBox( self.MIDIPageEffect, wx.ID_ANY, u"长音分析", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.EffectDoLongAnalysis.SetValue(True)
		MIDIPageEffect3.Add( self.EffectDoLongAnalysis, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.LongAnalysisThresholdPrompt = wx.StaticText( self.MIDIPageEffect, wx.ID_ANY, u"阈值（刻）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.LongAnalysisThresholdPrompt.Wrap( -1 )

		MIDIPageEffect3.Add( self.LongAnalysisThresholdPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.LongAnalysisThresholdSpin = wx.SpinCtrlDouble( self.MIDIPageEffect, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 1, 120, 40, 1 )
		self.LongAnalysisThresholdSpin.SetDigits( 0 )
		MIDIPageEffect3.Add( self.LongAnalysisThresholdSpin, 0, wx.ALL, 5 )


		MIDIPageEffectContainer.Add( MIDIPageEffect3, 0, wx.EXPAND, 5 )

		MIDIPageEffect4 = wx.FlexGridSizer( 0, 2, 0, 0 )
		MIDIPageEffect4.SetFlexibleDirection( wx.BOTH )
		MIDIPageEffect4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.MaxTickNotePrompt = wx.StaticText( self.MIDIPageEffect, wx.ID_ANY, u"单刻最大发音数：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.MaxTickNotePrompt.Wrap( -1 )

		MIDIPageEffect4.Add( self.MaxTickNotePrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.MaxTickNoteSpin = wx.SpinCtrl( self.MIDIPageEffect, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 1, 511, 255 )
		MIDIPageEffect4.Add( self.MaxTickNoteSpin, 0, wx.ALL, 5 )


		MIDIPageEffectContainer.Add( MIDIPageEffect4, 0, wx.EXPAND, 5 )

		MIDIPageEffect5 = wx.FlexGridSizer( 0, 2, 0, 0 )
		MIDIPageEffect5.SetFlexibleDirection( wx.BOTH )
		MIDIPageEffect5.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.WrapLengthPrompt = wx.StaticText( self.MIDIPageEffect, wx.ID_ANY, u"折行长度（格）：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.WrapLengthPrompt.Wrap( -1 )

		MIDIPageEffect5.Add( self.WrapLengthPrompt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.WrapLengthSpin = wx.SpinCtrl( self.MIDIPageEffect, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 1, 65535, 128 )
		MIDIPageEffect5.Add( self.WrapLengthSpin, 0, wx.ALL, 5 )


		MIDIPageEffectContainer.Add( MIDIPageEffect5, 1, wx.EXPAND, 5 )

		self.EffectFunctionBased = wx.CheckBox( self.MIDIPageEffect, wx.ID_ANY, u"基于函数的刻阵列（实验性）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.EffectFunctionBased.SetValue(True)
		MIDIPageEffectContainer.Add( self.EffectFunctionBased, 0, wx.ALL, 5 )


		self.MIDIPageEffect.SetSizer( MIDIPageEffectContainer )
		self.MIDIPageEffect.Layout()
		MIDIPageEffectContainer.Fit( self.MIDIPageEffect )
		self.MIDIPages.AddPage( self.MIDIPageEffect, u"效果与性能", False )
		self.MIDIPageFrontend = wx.ScrolledWindow( self.MIDIPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
		self.MIDIPageFrontend.SetScrollRate( 5, 5 )
		self.MIDIPageFrontend.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPageFrontendContainer = wx.BoxSizer( wx.VERTICAL )

		self.FrontendPicker = wx.Choicebook( self.MIDIPageFrontend, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.CHB_DEFAULT )
		self.FrontendPicker.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPageFrontendContainer.Add( self.FrontendPicker, 1, wx.EXPAND |wx.ALL, 5 )


		self.MIDIPageFrontend.SetSizer( MIDIPageFrontendContainer )
		self.MIDIPageFrontend.Layout()
		MIDIPageFrontendContainer.Fit( self.MIDIPageFrontend )
		self.MIDIPages.AddPage( self.MIDIPageFrontend, u"前端", False )
		self.MIDIPagePlugins = wx.ScrolledWindow( self.MIDIPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
		self.MIDIPagePlugins.SetScrollRate( 5, 5 )
		self.MIDIPagePlugins.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPagePluginsContainer = wx.BoxSizer( wx.VERTICAL )

		PluginsListChoices = []
		self.PluginsList = wx.CheckListBox( self.MIDIPagePlugins, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, PluginsListChoices, wx.LB_ALWAYS_SB|wx.LB_MULTIPLE )
		MIDIPagePluginsContainer.Add( self.PluginsList, 0, wx.ALL|wx.EXPAND, 5 )

		self.PluginsPicker = wx.Choicebook( self.MIDIPagePlugins, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.CHB_DEFAULT )
		MIDIPagePluginsContainer.Add( self.PluginsPicker, 1, wx.ALL|wx.EXPAND, 5 )


		self.MIDIPagePlugins.SetSizer( MIDIPagePluginsContainer )
		self.MIDIPagePlugins.Layout()
		MIDIPagePluginsContainer.Fit( self.MIDIPagePlugins )
		self.MIDIPages.AddPage( self.MIDIPagePlugins, u"插件", False )
		self.MIDIPageMiddles = wx.ScrolledWindow( self.MIDIPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
		self.MIDIPageMiddles.SetScrollRate( 5, 5 )
		self.MIDIPageMiddles.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPageMiddlesContainer = wx.BoxSizer( wx.VERTICAL )

		MiddlesListChoices = []
		self.MiddlesList = wx.CheckListBox( self.MIDIPageMiddles, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, MiddlesListChoices, wx.LB_ALWAYS_SB|wx.LB_MULTIPLE )
		MIDIPageMiddlesContainer.Add( self.MiddlesList, 0, wx.ALL|wx.EXPAND, 5 )

		self.MiddlesPicker = wx.Choicebook( self.MIDIPageMiddles, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.CHB_DEFAULT )
		MIDIPageMiddlesContainer.Add( self.MiddlesPicker, 1, wx.ALL|wx.EXPAND, 5 )


		self.MIDIPageMiddles.SetSizer( MIDIPageMiddlesContainer )
		self.MIDIPageMiddles.Layout()
		MIDIPageMiddlesContainer.Fit( self.MIDIPageMiddles )
		self.MIDIPages.AddPage( self.MIDIPageMiddles, u"中间件", False )
		self.MIDIPageAbout = wx.Panel( self.MIDIPages, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.MIDIPageAbout.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		MIDIPageAboutContainer = wx.BoxSizer( wx.VERTICAL )

		self.MIDIPageAboutHTML = wx.html.HtmlWindow( self.MIDIPageAbout, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.html.HW_SCROLLBAR_AUTO )
		MIDIPageAboutContainer.Add( self.MIDIPageAboutHTML, 1, wx.ALL|wx.EXPAND, 5 )


		self.MIDIPageAbout.SetSizer( MIDIPageAboutContainer )
		self.MIDIPageAbout.Layout()
		MIDIPageAboutContainer.Fit( self.MIDIPageAbout )
		self.MIDIPages.AddPage( self.MIDIPageAbout, u"关于", True )

		MainContainer.Add( self.MIDIPages, 1, wx.EXPAND |wx.ALL, 5 )

		Bottom = wx.FlexGridSizer( 0, 3, 0, 0 )
		Bottom.SetFlexibleDirection( wx.BOTH )
		Bottom.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.Run = wx.Button( self, wx.ID_ANY, u"生成", wx.DefaultPosition, wx.DefaultSize, 0 )
		Bottom.Add( self.Run, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.GoDefault = wx.Button( self, wx.ID_ANY, u"取消", wx.DefaultPosition, wx.DefaultSize, 0 )
		Bottom.Add( self.GoDefault, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.ProgressBar = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL|wx.GA_SMOOTH )
		self.ProgressBar.SetValue( 0 )
		Bottom.Add( self.ProgressBar, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		MainContainer.Add( Bottom, 0, wx.EXPAND, 5 )


		self.SetSizer( MainContainer )
		self.Layout()
		self.StatusBar = self.CreateStatusBar( 1, wx.STB_ELLIPSIZE_MIDDLE|wx.STB_SIZEGRIP, wx.ID_ANY )

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


