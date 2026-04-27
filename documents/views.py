from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from .models import Document, DocumentComment


@login_required
def document_list(request):
    my_docs = Document.objects.filter(owner=request.user)
    shared_docs = Document.objects.filter(shared_with=request.user)
    public_docs = Document.objects.filter(is_public=True)[:20]
    
    return render(request, 'documents/document_list.html', {
        'my_docs': my_docs,
        'shared_docs': shared_docs,
        'public_docs': public_docs,
    })


@login_required
def document_upload(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        category = request.POST.get('category', 'personal')
        is_public = request.POST.get('is_public') == 'on'
        file = request.FILES.get('file')
        
        if not file:
            messages.error(request, "Veuillez sélectionner un fichier.")
            return redirect('documents:document_upload')
        
        doc = Document.objects.create(
            title=title,
            description=description,
            category=category,
            owner=request.user,
            is_public=is_public,
            file=file,
        )
        
        messages.success(request, "Document uploadé avec succès!")
        return redirect('documents:document_detail', doc_id=doc.id)
    
    return render(request, 'documents/upload.html')


@login_required
def document_detail(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    comments = doc.comments.all()
    return render(request, 'documents/document_detail.html', {'document': doc, 'comments': comments})


@login_required
def document_download(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    doc.download_count += 1
    doc.save()
    return FileResponse(doc.file.open(), as_attachment=True, filename=doc.file.name.split('/')[-1])
