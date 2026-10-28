from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models.withdraw import db, WithdrawalRequest

withdrawal_bp = Blueprint('withdrawal', __name__)

POINTS_TO_IDR_RATE = 100  
MIN_WITHDRAWAL_POINTS = 500  # Minimum 500 poin baru bisa ditarik

@withdrawal_bp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'POST':
        try:
            points_to_redeem = int(request.form.get('points'))
        except (TypeError, ValueError):
            flash('Jumlah poin tidak valid.', 'error')
            return redirect(url_for('withdrawal.withdraw'))

        payment_method = request.form.get('payment_method')
        account_number = request.form.get('account_number')

        # Validasi ketentuan
        if points_to_redeem < MIN_WITHDRAWAL_POINTS:
            flash(f'Minimum penarikan adalah {MIN_WITHDRAWAL_POINTS} poin.', 'error')
            return redirect(url_for('withdrawal.withdraw'))

        if points_to_redeem > current_user.brainpoints:
            flash('Brainpoints Anda tidak mencukupi.', 'error')
            return redirect(url_for('withdrawal.withdraw'))

        # Hitung nominal rupiah
        amount_rupiah = (points_to_redeem / POINTS_TO_IDR_RATE) * 1000

        # Kurangi poin user
        current_user.brainpoints -= points_to_redeem

        # Buat record permintaan penarikan
        new_request = WithdrawalRequest(
            user_id=current_user.id,
            points_deducted=points_to_redeem,
            amount_rupiah=amount_rupiah,
            payment_method=payment_method,
            account_number=account_number,
            status='Pending'
        )
        
        db.session.add(new_request)
        db.session.commit()

        flash(f'Permintaan penarikan Rp {amount_rupiah:,.0f} berhasil dikirim dan sedang diproses!', 'success')
        return redirect(url_for('withdrawal.withdraw'))

    # Ambil riwayat penarikan user yang sedang login
    user_history = WithdrawalRequest.query.filter_by(user_id=current_user.id).order_by(WithdrawalRequest.created_at.desc()).all()
    
    return render_template('withdraw.html', history=user_history, rate=POINTS_TO_IDR_RATE)