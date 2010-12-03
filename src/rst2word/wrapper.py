'''
This file is part of docutils

Created on 26 oct. 2010
@author: diabeteman
'''
import win32com.client as WIN
from rst2word.constants import Constants as CST

class Excel:

    def __init__(self, filename):
        self.xlApp = WIN.dynamic.Dispatch("Excel.Application")
        self.xlApp.DisplayAlerts = 0 # disable confirmation requests
        self.xlApp.Workbooks.Open(filename)

    def show(self):
        # convenience when debugging
        self.xlApp.Visible = 1

    def copyCells(self):
        self.xlApp.ActiveWorkbook.ActiveSheet.Cells.Select()
        self.xlApp.Selection.Copy()

    def close(self):
        self.xlApp.Quit()


class Word:
    """
    Wrapper aroud Word 8 documents to make them easy to build.
    Has variables for the Applications, Document and Selection; 
    most methods add things at the end of the document
    """

    def __init__(self, templatefile=None):
        self.wordApp = WIN.dynamic.Dispatch("Word.Application")
        self.wordApp.DisplayAlerts = 0 # disable confirmation requests

        if templatefile == None:
            self.doc = self.wordApp.Documents.Add()
        else:
            self.doc = self.wordApp.Documents.Add(Template=templatefile)

        #set up the selection
        self.doc.Range(0, 0).Select()
        self.selection = self.wordApp.Selection

    def show(self):
        # convenience when debugging
        self.wordApp.Visible = 1

    def quit(self, saveChanges=False):
        self.wordApp.Quit(SaveChanges=saveChanges)

    def getStyleList(self):
        # returns a dictionary of the styles in a document
        self.styles = []
        stylecount = self.doc.Styles.Count
        for i in range(1, stylecount + 1):
            styleObject = self.doc.Styles(i)
            self.styles.append(styleObject.NameLocal)

        return self.styles

    def saveAs(self, filename):
        self.doc.SaveAs(filename)

    def printout(self):
        self.doc.PrintOut()

    def selectEnd(self):
        self.selection.Collapse(CST.wdCollapseEnd)

    def addText(self, text):
        self.selection.TypeText(text)
        self.selectEnd()

    def addStyledText(self, text, style):
        self.selection.Style = style
        self.selection.TypeText(text)
        self.selectEnd()
        self.selection.Style = CST.wdStyleDefaultParagraphFont


    def addTable(self, rows, cols):
        return self.doc.Tables.Add(Range=self.selection.Range, 
                                   NumRows=rows, 
                                   NumColumns=cols, 
                                   DefaultTableBehavior=0, 
                                   AutoFitBehavior=CST.wdAutoFitContent)


    def pasteExcelTable(self):
        self.selection.PasteExcelTable(False, #link with excel ?
                                       False, #word formatting ?
                                       False) #RTF ?

    def setDocProperty(self, name, value):
        if name in ["Title", "Subject", "Author", "Comments", "Revision", "Company"]:
            self.doc.BuiltInDocumentProperties[name] = value
        else:
            try:
                self.doc.CustomDocumentProperties[name] = value
            except:
                self.doc.CustomDocumentProperties.Add(name, False, 4, value)

    def getDocProperty(self, name):
        try:
            if name in ["Title", "Subject", "Author", "Comments", "Revision number", "Company"]:
                return self.doc.BuiltInDocumentProperties[name].Value
            else:
                return self.doc.CustomDocumentProperties[name].Value
        except:
            return ""

    def insertField(self, doc_property_name):
        self.selection.Fields.Add(Range=self.selection.Range, 
                                  Type=CST.wdFieldEmpty, 
                                  Text="DOCPROPERTY  %s " % doc_property_name, 
                                  PreserveFormatting=True)

    def setStyle(self, style):
        self.selection.Style = style

    def setFont(self, font):
        self.selection.Font.__setattr__(font, CST.wdToggle)


    def insertTableOfContents(self, depth=3):
        """
        Function Add(Range As Range, [UseHeadingStyles], [UpperHeadingLevel], [LowerHeadingLevel], 
        [UseFields], [TableID], [RightAlignPageNumbers], [IncludePageNumbers], [AddedStyles], 
        [UseHyperlinks], [HidePageNumbersInWeb], [UseOutlineLevels]) As TableOfContents
        """
        self.doc.TablesOfContents.Add(Range=self.selection.Range, UseHeadingStyles=True,
                                      UpperHeadingLevel=1, LowerHeadingLevel=depth, UseFields=True)
        self.selectEnd()

    def updateFields(self):
        for table in self.doc.TablesOfContents:
            table.Update()

        self.doc.Range().Fields.Update()

        for shape in self.doc.Shapes:
            if shape.TextFrame.HasText:
                shape.TextFrame.TextRange.Fields.Update()

        for section in self.doc.Sections:
            for header in section.Headers:
                header.Range.Fields.Update()
                for shape in header.Shapes:
                    if shape.TextFrame.HasText:
                        shape.TextFrame.TextRange.Fields.Update()
            for footer in section.Footers:
                footer.Range.Fields.Update()
                for shape in footer.Shapes:
                    if shape.TextFrame.HasText:
                        shape.TextFrame.TextRange.Fields.Update()

    def insertPageBreak(self):
        self.selection.InsertBreak(7)
        self.selectEnd()

    def newParagraph(self):
        self.selection.TypeParagraph()

    def setAlignment(self, alignment):
        self.selection.ParagraphFormat.Alignment = alignment

    def insertImage(self, image_path):
        image = self.selection.InlineShapes.AddPicture(FileName=image_path,
                                                       LinkToFile=False, SaveWithDocument=True)
        self.selectEnd()

        return image

    def addCaption(self, text, figure, auto=False, label="Figure"):
        if auto:
            figure.Select()
            self.wordApp.Selection.InsertCaption(Label=label, TitleAutoText="", Title=" " + text,
                                                 Position=1, ExcludeLabel=0)
        else:
            self.selection.Style = CST.wdStyleCaption

        self.selectEnd()
        self.newParagraph()
        self.clearFormatting()

    def move(self, direction, unit=CST.wdCell, count=1):
        if direction == "left":
            self.selection.MoveLeft(Unit=unit, Count=count)
        elif direction == "right":
            self.selection.MoveRight(Unit=unit, Count=count)
        elif direction == "up":
            self.selection.MoveUp(Unit=unit, Count=count)
        elif direction == "down":
            self.selection.MoveDown(Unit=unit, Count=count)
    
    def formatTables(self, style=CST.wdTableFormatProfessional, fit=CST.wdAutoFitContent, align=CST.wdAlignRowCenter):
        for t in self.doc.Tables:
            self.formatTable(t, style, fit, align)
    
    def formatTable(self, table, latteral_padding=0.25, vertical_padding=0.15, 
                    border=False, first_row_bg_color=CST.wdColorAutomatic, 
                    fit=CST.wdAutoFitContent, align=CST.wdAlignRowCenter):
        
        table.TopPadding = CentimetersToPoints(vertical_padding)
        table.BottomPadding = CentimetersToPoints(vertical_padding)
        table.LeftPadding = CentimetersToPoints(latteral_padding)
        table.RightPadding = CentimetersToPoints(latteral_padding)
            
        if first_row_bg_color != CST.wdColorAutomatic:
            first_row = table.Rows.Item(1)
            first_row.Cells.Shading.Texture = CST.wdTextureNone
            first_row.Cells.Shading.ForegroundPatternColor = CST.wdColorAutomatic
            first_row.Cells.Shading.BackgroundPatternColor = first_row_bg_color
        
        if border:
            setBorder(table.Borders(CST.wdBorderLeft))
            setBorder(table.Borders(CST.wdBorderRight))
            setBorder(table.Borders(CST.wdBorderTop))
            setBorder(table.Borders(CST.wdBorderBottom))
            setBorder(table.Borders(CST.wdBorderHorizontal))
            setBorder(table.Borders(CST.wdBorderVertical))
                
        table.Rows.Alignment = align
        table.AutoFitBehavior(fit)
    
        self.selectEnd()
    
    def fitTables(self, fit=CST.wdAutoFitContent):
        for table in self.doc.Tables:
            table.AutoFitBehavior(fit)

    def insertBookmark(self, name):
        self.doc.Bookmarks.Add(Range=self.selection.Range, Name=name)
    
    def insertHyperlink(self, text, target):
        self.doc.Hyperlinks.Add(Anchor=self.selection.Range,
                                Address=target, TextToDisplay=text)
    
    def convertToInternalHyperlink(self, link):
        target = link.Address
        
        link.Range.Fields(1).Result.Select()
        link.Delete()
        self.doc.Hyperlinks.Add(Anchor=self.selection.Range,
                                SubAddress=target, Address="")
        self.selectEnd()
    
    def getHyperlinks(self):
        return self.doc.Hyperlinks
    
    def getCurrentPosition(self):
        return self.selection.Range.Start
    
    def clearFormatting(self):
        self.selection.ClearFormatting()

    def resetListStartNumber(self):
        list_template = self.selection.Style.ListTemplate
        list_lvl = list_template.ListLevels(1)
        list_lvl.StartAt = 1
        list_lvl.LinkedStyle = self.selection.Style
        self.selection.Range.ListFormat.ApplyListTemplate(ListTemplate=list_template, 
                                                                   ContinuePreviousList=False,
                                                                   ApplyTo=CST.wdListApplyToWholeList, 
                                                                   DefaultListBehavior=CST.wdWord10ListBehavior)

    def addOLEObject(self, filename, classType="PowerPoint.Show.8"):
        shape = self.selection.InlineShapes.AddOLEObject(ClassType=classType, 
                                                         FileName=file, 
                                                         LinkToFile=False, 
                                                         DisplayAsIcon=False)
        shape.LockAspectRatio = -1
        shape.Width = (self.doc.PageSetup.PageWidth 
                     - self.doc.PageSetup.RightMargin 
                     - self.doc.PageSetup.LeftMargin)
        self.selectEnd()

def CentimetersToPoints(centimeters):
    return centimeters * 28.35

def setBorder(b):
    b.LineStyle = CST.wdLineStyleSingle
    b.LineWidth = CST.wdLineWidth050pt
    b.Color = CST.wdColorAutomatic
    
def setNoBorder(b):
    b.LineStyle = CST.wdLineStyleNone