from datetime import datetime
import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Appointment, ContactMessage, Doctor, PatientProfile, Service, Slot


# =========================================================
# ГЛАВНАЯ
# =========================================================


def main(request):
  return render(request, 'booking/main.html')


# =========================================================
# РЕГИСТРАЦИЯ
# =========================================================


def register(request):
  if request.user.is_authenticated:
    return redirect('main')

  if request.method == 'POST':
    username = request.POST.get('username', '').strip()
    iin = request.POST.get('iin', '').strip()
    full_name = request.POST.get('full_name', '').strip()
    phone = request.POST.get('phone', '').strip()
    password = request.POST.get('password', '')
    password2 = request.POST.get('password2', '')
    sms_code = request.POST.get('sms_code', '').strip()

    if not all([username, iin, full_name, phone, password, password2, sms_code]):
      return render(
          request,
          'booking/register.html',
          {'error': 'Заполните все поля.'},
      )

    if len(iin) != 12 or not iin.isdigit():
      return render(
          request,
          'booking/register.html',
          {'error': 'ИИН должен содержать ровно 12 цифр.'},
      )

    if password != password2:
      return render(
          request, 'booking/register.html', {'error': 'Пароли не совпадают.'}
      )

    if sms_code != '1111':
      return render(
          request,
          'booking/register.html',
          {
              'error': (
                  'Неверный SMS-код. Для демонстрации используйте 1111.'
              )
          },
      )

    if User.objects.filter(username=username).exists():
      return render(
          request,
          'booking/register.html',
          {'error': 'Такой логин уже существует.'},
      )

    if PatientProfile.objects.filter(iin=iin).exists():
      return render(
          request,
          'booking/register.html',
          {'error': 'Пациент с таким ИИН уже зарегистрирован.'},
      )

    if PatientProfile.objects.filter(phone=phone).exists():
      return render(
          request,
          'booking/register.html',
          {'error': 'Этот номер телефона уже зарегистрирован.'},
      )

    try:
      user = User.objects.create_user(username=username, password=password)

      PatientProfile.objects.create(
          user=user, iin=iin, full_name=full_name, phone=phone
      )

    except IntegrityError:
      return render(
          request,
          'booking/register.html',
          {
              'error': (
                  'Не удалось создать аккаунт. Проверьте логин, ИИН и номер'
                  ' телефона.'
              )
          },
      )

    login(request, user)

    return redirect('main')

  return render(request, 'booking/register.html')


# =========================================================
# ВХОД
# =========================================================


def login_view(request):
  if request.user.is_authenticated:
    return redirect('main')

  if request.method == 'POST':
    username = request.POST.get('username', '').strip()

    password = request.POST.get('password', '')

    user = authenticate(request, username=username, password=password)

    if user is not None:
      login(request, user)

      return redirect('main')

    return render(
        request, 'booking/login.html', {'error': 'Неверный логин или пароль.'}
    )

  return render(request, 'booking/login.html')


# =========================================================
# ВЫХОД
# =========================================================


def logout_view(request):
  if request.method == 'POST':
    logout(request)

  return redirect('main')


# =========================================================
# ПРОФИЛЬ
# =========================================================


@login_required(login_url='/login/')
def profile(request):
  profile, created = PatientProfile.objects.get_or_create(
      user=request.user,
      defaults={
          'iin': str(request.user.id).zfill(12),
          'full_name': request.user.get_full_name() or request.user.username,
          'phone': f'not-set-{request.user.id}',
      },
  )

  return render(request, 'booking/profile.html', {'profile': profile})

@login_required(login_url='/login/')
def update_phone(request):
    if request.method == 'POST':
        new_phone = request.POST.get('phone', '').strip()
        if new_phone:
            profile, created = PatientProfile.objects.get_or_create(user=request.user)
            
            # Проверяем, не занят ли номер другим пользователем
            if PatientProfile.objects.filter(phone=new_phone).exclude(user=request.user).exists():
                messages.error(request, 'Этот номер телефона уже используется другим пользователем.')
            else:
                profile.phone = new_phone
                profile.save()
                messages.success(request, 'Номер телефона успешно обновлен!')
                
    return redirect('profile')


def home(request):
  doctor_id = request.GET.get('doctor')
  service_id = request.GET.get('service')
  date_str = request.GET.get('date')

  doctors = Doctor.objects.all()

  if doctor_id:
    doctors = doctors.filter(id=doctor_id)

  if service_id:
    doctors = doctors.filter(service__id=service_id).distinct()

  if date_str:
    try:
      selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
      selected_date = timezone.now().date()
  else:
    selected_date = timezone.now().date()

  for doctor in doctors:
    slots = Slot.objects.filter(
        doctor=doctor, is_available=True, date=selected_date
    )
    doctor.available_slots = slots.order_by('time')

  if request.method == 'POST':
    slot_id = request.POST.get('slot')
    service_id = request.POST.get('service')
    if slot_id:
      # Перенаправляем на страницу подтверждения вместо моментального создания
      return redirect('booking_confirm', slot_id=slot_id, service_id=service_id or 0)

  context = {
      'doctors': Doctor.objects.all(),
      'filtered_doctors': doctors,
      'services': Service.objects.all(),
  }
  return render(request, 'booking/home.html', context)


# =========================================================
# ПОДТВЕРЖДЕНИЕ ЗАПИСИ
# =========================================================


def booking_confirm_view(request, slot_id, service_id):
  slot = get_object_or_404(Slot, id=slot_id)
  service = (
      get_object_or_404(Service, id=service_id)
      if service_id and service_id != 0
      else None
  )
  doctor = slot.doctor

  if request.method == 'POST':
    slot.is_available = False
    slot.save()

    user = request.user if request.user.is_authenticated else None

    # Создаем запись в базе только после подтверждения
    appointment = Appointment.objects.create(
        user=user, doctor=doctor, slot=slot, service=service
    )

    if not request.user.is_authenticated:
      request.session['last_appointment_id'] = appointment.id

    return redirect('booking_success', appointment_id=appointment.id)

  context = {
      'slot': slot,
      'service': service,
      'doctor': doctor,
  }
  return render(request, 'booking/booking_confirm.html', context)


# =========================================================
# УСПЕШНАЯ ЗАПИСЬ
# =========================================================


def booking_success(request, appointment_id):
  if request.user.is_authenticated:
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'service', 'slot'),
        id=appointment_id,
        user=request.user,
    )

  else:
    last_appointment_id = request.session.get('last_appointment_id')

    if last_appointment_id != appointment_id:
      return redirect('home')

    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'service', 'slot'),
        id=appointment_id,
    )

  return render(
      request, 'booking/booking_success.html', {'appointment': appointment}
  )


# =========================================================
# МОИ ЗАПИСИ
# =========================================================


@login_required(login_url='/login/')
def appointments(request):
  appointments_list = (
      Appointment.objects.filter(user=request.user)
      .select_related('doctor', 'service', 'slot')
      .order_by('slot__date', 'slot__time')
  )

  return render(
      request, 'booking/appointments.html', {'appointments': appointments_list}
  )


# =========================================================
# ОТМЕНА ЗАПИСИ
# =========================================================


@login_required(login_url='/login/')
def cancel_appointment(request, appointment_id):
  appointment = get_object_or_404(
      Appointment, id=appointment_id, user=request.user
  )

  if request.method == 'POST':
    slot = appointment.slot

    slot.is_available = True

    slot.save(update_fields=['is_available'])

    appointment.delete()

  return redirect('appointments')


# =========================================================
# ПОИСК СВОБОДНЫХ СЛОТОВ
# =========================================================


def search_slots(request):
  doctor_id = request.GET.get('doctor')

  service_id = request.GET.get('service')

  date = request.GET.get('date')

  slots = (
      Slot.objects.filter(is_available=True, appointment__isnull=True)
      .select_related('doctor')
      .order_by('date', 'time')
  )

  if doctor_id:
    slots = slots.filter(doctor_id=doctor_id)

  if service_id:
    service = get_object_or_404(Service, id=service_id)

    if service.doctor_id:
      slots = slots.filter(doctor_id=service.doctor_id)

  if date:
    slots = slots.filter(date=date)

  slots = slots[:100]

  data = []

  for slot in slots:
    data.append({
        'id': slot.id,
        'doctor_id': slot.doctor.id,
        'doctor_name': slot.doctor.name,
        'specialty': slot.doctor.specialty,
        'date': slot.date.strftime('%d.%m.%Y'),
        'time': slot.time.strftime('%H:%M'),
    })

  return JsonResponse({'slots': data})


# =========================================================
# УСЛУГИ
# =========================================================


def services(request):
  services_list = Service.objects.select_related('doctor').all()

  return render(request, 'booking/services.html', {'services': services_list})


def contacts(request):
  error_message = None

  if request.method == 'POST':
    name = request.POST.get('name', '').strip()
    contact_info = request.POST.get('contact_info', '').strip()
    message = request.POST.get('message', '').strip()

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    phone_digits = re.sub(r'\D', '', contact_info)

    is_email = re.match(email_regex, contact_info)
    is_phone = len(phone_digits) >= 6

    if not name or not contact_info or not message:
      error_message = 'Пожалуйста, заполните все поля формы.'
    elif not is_email and not is_phone:
      error_message = (
          'Введите корректный Email (например, example@mail.com) или номер'
          ' телефона.'
      )
    else:
      ContactMessage.objects.create(
          name=name, contact_info=contact_info, message=message
      )
      return redirect('/contacts/?success=1')

  success = request.GET.get('success')
  return render(
      request,
      'booking/contacts.html',
      {'success': success, 'error': error_message},
  )