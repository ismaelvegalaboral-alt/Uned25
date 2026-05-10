from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from .models import VacationRequest
from .permissions import can_access_request


@login_required
def supporting_document_download(request, pk):
    vacation_request = get_object_or_404(
        VacationRequest.objects.select_related('employee', 'employee__user'),
        pk=pk,
    )

    if not can_access_request(request.user, vacation_request):
        raise Http404('Documento no encontrado.')

    if not vacation_request.supporting_document:
        raise Http404('Esta solicitud no tiene justificante.')

    return FileResponse(
        vacation_request.supporting_document.open('rb'),
        as_attachment=True,
        filename=vacation_request.supporting_document.name.split('/')[-1],
    )
