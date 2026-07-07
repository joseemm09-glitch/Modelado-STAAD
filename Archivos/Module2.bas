Attribute VB_Name = "Module2"
Sub ExportarTodoParaAntigravity()
    Dim selectorCarpeta As FileDialog
    Dim rutaDestino As String
    Dim componenteVBA As Object
    Dim extension As String
    Dim rutaCompleta As String
    Dim contador As Integer

    ' 1. Configurar el selector de carpetas visual
    Set selectorCarpeta = Application.FileDialog(msoFileDialogFolderPicker)
    selectorCarpeta.Title = "Selecciona la carpeta para guardar el código de Antigravity"
    
    If selectorCarpeta.Show = -1 Then
        rutaDestino = selectorCarpeta.SelectedItems(1) & "\"
    Else
        MsgBox "Exportación cancelada por el usuario.", vbExclamation, "Proceso Interrumpido"
        Exit Sub
    End If

    ' 2. Verificar que tenemos acceso al proyecto de VBA
    On Error Resume Next
    Dim pruebaAcceso As Object
    Set pruebaAcceso = ThisWorkbook.VBProject
    If Err.Number <> 0 Then
        MsgBox "Error: Debes habilitar el 'Acceso de confianza al modelo de objetos de proyectos de VBA'" & vbCrLf & _
               "en las opciones del Centro de Confianza de Excel.", vbCritical, "Falta Permiso de Seguridad"
        Exit Sub
    End If
    On Error GoTo 0

    ' 3. Recorrer y exportar cada componente estructurado
    contador = 0
    For Each componenteVBA In ThisWorkbook.VBProject.VBComponents
        Select Case componenteVBA.Type
            Case 1 ' Modulo estándar (.bas)
                extension = ".bas"
            Case 2 ' Módulo de clase (.cls)
                extension = ".cls"
            Case 3 ' UserForm / Formulario (.frm)
                extension = ".frm"
            Case Else
                ' Omitimos el código interno de las hojas de cálculo individuales (ThisWorkbook, Hoja1, etc.)
                ' para mantener limpio tu espacio de trabajo en Antigravity.
                extension = ""
        End Select
        
        ' Si el componente es exportable, guardarlo en la carpeta
        If extension <> "" Then
            rutaCompleta = rutaDestino & componenteVBA.Name & extension
            componenteVBA.Export rutaCompleta
            contador = contador + 1
        End If
    Next componenteVBA

    ' 4. Notificación de éxito
    MsgBox "¡Excelente! Se han exportado " & contador & " componentes con éxito." & vbCrLf & _
           "Ruta: " & rutaDestino, vbInformation, "Proceso Completado"
End Sub

