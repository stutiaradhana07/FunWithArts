from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Workshop, Booking
from .serializers import WorkshopSerializer, BookingSerializer


@api_view(['GET'])
def workshop_list(request):
    workshops = Workshop.objects.all().order_by('date', 'time')
    serializer = WorkshopSerializer(workshops, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def workshop_detail(request, pk):
    workshop = get_object_or_404(Workshop, pk=pk)
    serializer = WorkshopSerializer(workshop, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def create_booking(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Login required'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = BookingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    workshop = serializer.validated_data['workshop']
    seats = serializer.validated_data['seats']

    if seats > workshop.available_slots:
        return Response(
            {'error': 'Not enough seats available.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    workshop.available_slots -= seats
    workshop.save(update_fields=['available_slots'])
    booking = serializer.save(user=request.user)
    return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
