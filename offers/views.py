from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model


from guardian.shortcuts import assign_perm
from guardian.decorators import permission_required_or_403

from .models import Offer
from .forms import MakeOfferForm


class OfferListView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = 'offers.view_offer'
    template_name = 'offers/offers.html'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        context = {
            'offers': None,
        }
        if user.has_perm('offers.add_offer'):
            context['offers'] = Offer.objects.filter(
                client=self.request.user,
                status=Offer.STATUS_PENDING
            ).order_by('created_datetime')

        elif user.has_perm('offers.change_offer'):
            context['offers'] = Offer.objects.filter(
                sitter=self.request.user,
                status=Offer.STATUS_PENDING
            ).order_by('created_datetime')
        
        return render(self.request, self.template_name, context)


class OfferAnswersListView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = 'offers.view_offer'
    template_name = 'offers/answers.html'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        context = {
            'offers': None,
        }
        if user.has_perm('offers.add_offer'):
            context['offers'] = Offer.objects.filter(
                client=self.request.user,
                status__in=[Offer.STATUS_ACCEPTED, Offer.STATUS_DECLINED]
            ).order_by('status')

        elif user.has_perm('offers.change_offer'):
            context['offers'] = Offer.objects.filter(
                sitter=self.request.user,
                status__in=[Offer.STATUS_ACCEPTED, Offer.STATUS_DECLINED]
            ).order_by('status')
        
        return render(self.request, self.template_name, context)


class MakeOfferView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = 'offers.add_offer'
    template_name = 'offers/form.html'
    form_class = MakeOfferForm
    success_url = reverse_lazy('list')

    def get(self, request, sitter_id, *args, **kwargs):
        get_object_or_404(get_user_model(), pk=sitter_id)
        form = self.form_class()
        context = {
            'form': form,
            'sitter_id': sitter_id,
        }
        return render(request, self.template_name, context)

    def post(self, request, sitter_id, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            offer = form.save(commit=False)
            offer.client = request.user
            offer.sitter = get_object_or_404(get_user_model(), pk=sitter_id)
            offer.save()

            # Apply permissions
            assign_perm('offers.change_offer', offer.client, offer)

            return redirect(self.success_url)

        context = {
            'form': form,
            'sitter_id': sitter_id,
        }
        return render(request, self.template_name, context)


@login_required
@permission_required_or_403('offers.change_offer')
def accept_offer_view(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    if not request.user.pk == offer.sitter.pk:
        raise PermissionDenied
    offer.status = Offer.STATUS_ACCEPTED
    offer.save()
    return redirect(reverse_lazy('offers:offers'))


@login_required
@permission_required_or_403('offers.change_offer')
def decline_offer_view(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    if not request.user.pk == offer.sitter.pk:
        raise PermissionDenied
    offer.status = Offer.STATUS_DECLINED
    offer.save()
    return redirect(reverse_lazy('offers:offers'))
