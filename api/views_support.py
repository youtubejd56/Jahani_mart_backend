from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import SupportTicket, TicketReply, FAQ, Order
from .serializers import SupportTicketSerializer, TicketReplySerializer, FAQSerializer
import random
import string
from django.contrib.auth.models import User

# Admin views for support tickets
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_all_tickets(request):
    """Admin: Get all support tickets"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    status_filter = request.query_params.get('status')
    if status_filter:
        tickets = SupportTicket.objects.filter(status=status_filter).order_by('-created_at')
    else:
        tickets = SupportTicket.objects.all().order_by('-created_at')
    
    serializer = SupportTicketSerializer(tickets, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_ticket_detail(request, ticket_id):
    """Admin: Get ticket details"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id)
    except SupportTicket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SupportTicketSerializer(ticket)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_ticket_reply(request, ticket_id):
    """Admin: Reply to a support ticket"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id)
    except SupportTicket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    
    message = request.data.get('message')
    if not message:
        return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create reply as admin
    reply = TicketReply.objects.create(
        ticket=ticket,
        user=request.user,
        message=message,
        is_admin_reply=True
    )
    
    # Update ticket status
    new_status = request.data.get('status', 'In Progress')
    ticket.status = new_status
    ticket.save()
    
    return Response(TicketReplySerializer(reply).data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_update_ticket_status(request, ticket_id):
    """Admin: Update ticket status"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id)
    except SupportTicket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    
    new_status = request.data.get('status')
    if new_status:
        ticket.status = new_status
        ticket.save()
    
    serializer = SupportTicketSerializer(ticket)
    return Response(serializer.data)


# Support Ticket Views
def generate_ticket_id():
    return 'TKT' + ''.join(random.choices(string.digits, k=8))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def support_tickets(request):
    if request.method == 'GET':
        tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
        serializer = SupportTicketSerializer(tickets, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = SupportTicketSerializer(data=request.data)
        if serializer.is_valid():
            ticket = serializer.save(user=request.user, ticket_id=generate_ticket_id())
            return Response(SupportTicketSerializer(ticket).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def support_ticket_detail(request, ticket_id):
    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id, user=request.user)
    except SupportTicket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = SupportTicketSerializer(ticket)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ticket_reply(request, ticket_id):
    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id, user=request.user)
    except SupportTicket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    
    message = request.data.get('message')
    if not message:
        return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    reply = TicketReply.objects.create(ticket=ticket, user=request.user, message=message)
    
    if ticket.status == 'Open':
        ticket.status = 'In Progress'
        ticket.save()
    
    return Response(TicketReplySerializer(reply).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def faq_list(request):
    category = request.query_params.get('category')
    if category:
        faqs = FAQ.objects.filter(category=category, is_active=True)
    else:
        faqs = FAQ.objects.filter(is_active=True)
    serializer = FAQSerializer(faqs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_support_ticket(request):
    ticket_type = request.data.get('ticket_type')
    subject = request.data.get('subject')
    description = request.data.get('description')
    order_id = request.data.get('order_id')
    priority = request.data.get('priority', 'Medium')
    
    if not all([ticket_type, subject, description]):
        return Response({'error': 'Ticket type, subject, and description are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    order = None
    if order_id:
        try:
            order = Order.objects.get(order_id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    ticket = SupportTicket.objects.create(
        user=request.user,
        ticket_id=generate_ticket_id(),
        ticket_type=ticket_type,
        subject=subject,
        description=description,
        order=order,
        priority=priority
    )
    
    return Response(SupportTicketSerializer(ticket).data, status=status.HTTP_201_CREATED)
