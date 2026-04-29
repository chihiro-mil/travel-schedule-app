from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from django.db.models import  Q
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime
from django.utils.dateparse import parse_date
from django.forms import inlineformset_factory
from app.models import Plan
from django.utils import timezone
from copy import deepcopy
from django.urls import reverse


from .forms import (
    RegisterForm,
    LoginForm,
    ScheduleForm,
    PlanForm,
    ChangeUsernameForm, 
    ChangeEmailForm,
    CustomPasswordChangeForm,
    BasePictureFormSet,
    BaseLinkFormSet,
    PictureForm,
    LinkForm,
)

from .models import User, Schedule, Plan, Link, Picture, TransportationMethod

from datetime import timedelta
from datetime import datetime, time

from collections import defaultdict

# from django.views import ListView
# from django.http import HttpResponse

#ビューの役割：フォームがチェック内容をもとに処理の流れを決める

#portfolio
def index_view(request):
    return render(request, 'app/index.html')


#アカウント登録
def register_view(request):
    if request.method == 'POST': #フォーム送信が行われた時
        form = RegisterForm(request.POST) #forms.pyに定義されたフォームクラス（RegisterForm）、request.POSTで送信されたデータを渡してオブジェクト作る
        if form.is_valid(): #バリエーションでフォーム入力内容チェック
            user = form.save(commit=False) #commit=Falseはデータベースに保存せずにオブジェクトだけ作る
            user.set_password(form.cleaned_data['password']) #set_password()はパスワードをハッシュ化（暗号化）して保存するためのメゾット 必須処理
            user.save() #パスワードがハッシュ化（暗号化）終わったあとでデータベースに保存
            login(request, user) #ユーザー登録した後にそのままログイン状態にする
            return redirect('app:home') #登録完了後、ホーム画面へ移動
    else: #最初からフォームを開いた場合（GETメゾットの時）
        form = RegisterForm() #空のフォームを作ってHTMLに渡す
    return render(request, 'app/register.html', {'form': form}) #render()はテンプレを表示する関数、app/register.htmlでアカウント登録画面表示、{'form': form}はテンプレへデータを渡す{{form}}で使える
    
#ログイン
def login_view(request): #requestの中にPOST/GETなのか、フォームで送られた値、ログインしているユーザー情報　など全部入っている
    if request.method == 'POST': #フォーム送信が行われた時
        form = LoginForm(request.POST) #forms.pyに定義されたフォームクラス（LoginForm）request.POSTで送信されたデータを渡してオブジェクト作る
        if form.is_valid(): #バリエーションでフォーム入力内容チェック
            email = form.cleaned_data['email'] #cleaned_dataはバリエーションを通ったキレイなデータ　必ずcleaned_dataから取り出す
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password) #authenticate()はDjangoのログイン判定係。Userテーブル探す、emailが一致するユーザーみつける、保存されているパスワードハッシュと入力したパスワードをハッシュ化を比較、合っていればUserオブジェクト返す
            
            if user is not None: #userに値が入っている→ログイン可能なユーザー見つかった、not None→メールorパスワードが間違っていない時
                login(request, user) #ログイン状態にする　セッションにユーザーIDを保存、request.userでいつでもユーザーにアクセスできるように
                return redirect('app:home') #ログインに成功したらホーム画面へ
            else:
                form.add_error(None, 'メールアドレスまたはパスワードが間違っています') #Noneの時、メールかパスワードが違うときにフォーム全体のエラー（Noneは各フィールドには紐づかない）
    else:
        form = LoginForm() #空のフォームを作ってHTMLに渡す
    return render(request, 'app/login.html', {'form': form}) #render()はテンプレを表示する関数、app/login.htmlでログイン画面表示、{'form': form}はテンプレへデータを渡す{{form}}で使える


#マイページ設定画面
@login_required #ログインしている人にだけ、このページを見られるようにする
def mypage_view(request):
    request.user.refresh_from_db() #ログイン中のユーザー情報をもう一度データベースから取り出して最新状態にする
    
    referer = request.META.get('HTTP_REFERER') #直前に見ていたURLをヘッダから取り出す。戻るボタンに使用できる
    return render(request, 'app/mypage.html', {
        'user': request.user,
        'back_url': referer
    }) #'user'：テンプレート側でユーザーネームを表示、'back_url':戻るボタン用

#ユーザー名変更画面
@login_required
def change_username_view(request):
    if request.method == 'POST':
        form = ChangeUsernameForm(request.POST, instance=request.user) #request.POSTの入力値とrequest.userのログイン中のユーザーを渡す。instanceで上書更新する意味になる
        if form.is_valid(): #フォームのバリエーションを実行
            form.save() #バリエーションOKなら、request.userのnameフィールドが置き換わってDBに保存
            request.user.refresh_from_db() #保存し終わった最新のユーザー情報を取り出す
            messages.success(request, 'ユーザー名を変更しました') #次の画面で「ユーザーを変更しました」のフラッシュメッセージが表示できるように
            return redirect('app:mypage') #マイページへ戻るリダイレクト
    else:
        form = ChangeUsernameForm()
    return render(request, 'app/change_username.html', {'form': form})

#メールアドレス変更画面
@login_required
def change_email_view(request):
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            request.user.refresh_from_db()
            messages.success(request, 'メールアドレスを変更しました')
            return redirect('app:mypage')
    else:
        form = ChangeEmailForm(instance=request.user)
        form.initial["email"] = ""
    return render(request, 'app/change_email.html', {'form': form})
    
#パスワード変更画面
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST) #パスワード変更フォームはどのユーザーのパスワードを変えるかを知る必要があるのでuser=request.userを必ず渡す
        if form.is_valid():
            user = form.save() #フォームの中で、現在のパスワードチェック・新パスワードのバリエーションを通してからハッシュ化して保存。戻り値として変更後のユーザーオブジェクトが返る
            request.user.refresh_from_db()
            update_session_auth_hash(request, user) #通常、パスワードが変更されると強制ログアウトされることがある。update_session_auth_hashを呼ぶとパスワードが変更されてもログイン状態は維持してくれる。
            messages.success(request, 'パスワードを変更しました')
            return redirect('app:mypage')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'app/change_password.html', {'form': form})

#ログアウト
def logout_view(request):
    logout(request)
    return redirect('app:login')

#ホーム画面（予定表一覧画面）
@login_required
def home_view(request):
    sort = request.GET.get('sort', 'date') #sort(並び替え) URLに?sort=updatedと書いてあればupdatadが入る　URLに何も指定がなければdateを使う
    
    if sort == 'updated': #更新順にした時
        schedules = Schedule.objects.filter(user=request.user).order_by('-updated_at') #-updated_atで最新が一番上になる
        sort_label ='予定日降順'
        next_sort = 'date'
    else: #更新順以外の時
        schedules = Schedule.objects.filter(user=request.user).order_by('-trip_start_date') #-trip_start_dateで一番後の予定が一番上に表示
        sort_label = '更新順'
        next_sort = 'updated'
        
    if request.method == 'POST': #POSTの時
        form = ScheduleForm(request.POST) #request.POSTの中に旅行タイトル、旅行期間の入力内容が入っている
        if form.is_valid(): #フォームのバリエーションチェックを実行
            schedule = form.save(commit=False) #form.save()で本来はDBに保存するが、commit=Falseで一旦保存せずにscheduleオブジェクトだけ作成(この時点では予定表とユーザーが紐づいていないため、一旦入力されたオブジェクトだけ作成)
            schedule.user = request.user #外部キーをセット　今ログイン(request.user)している人の予定だと紐づける。
            schedule.save() #userをセットした後初めてDBに保存。scheduleテーブルに1行追加
            return redirect('app:plan_create_or_edit', schedule_id=schedule.id) #保存が終わったら、予定の中身を追加する画面に移動。schedule_id=schedule.idで今作った予定表のIDをURLパラメータとして渡している
        else: #バリエーションエラーの時
            no_schedules = not schedules.exists() #not schedules.existsで予定がない→Ttue、予定がある→False まだ予定がありませんなどのメッセージを出すかのフラグ作成
            return render(request, 'app/home.html', {
                'form': form, #エラーの付いたformをそのままテンプレートに渡す
                'schedules': schedules,
                'sort_label': sort_label,
                'next_sort': next_sort,
                'show_add_modal': True, #モーダルを開いたままにする
                'no_schedules': no_schedules,
            })
    else: #GETの時
        form = ScheduleForm()
        no_schedules = not schedules.exists() #not schedules.existsで予定がない→Ttue、予定がある→False まだ予定がありませんなどのメッセージを出すかのフラグ作成
        return render(request, 'app/home.html', {
            'form': form, #新しい予定表を追加するフォーム
            'schedules': schedules, #ホーム画面で一覧表示している旅行リスト
            'sort_label': sort_label, #並び替えボタンの表示用リスト
            'next_sort': next_sort, #並び替えボタンを押した時に、予定日順→更新順・更新順→予定日順と切り替え表示を実現している
            'show_add_modal': False, #最初からモーダルは開かない
            'no_schedules': no_schedules, #予定が一件もないかチェック
        })
    
#予定表のタイトル・旅行期間編集ケバブ
def edit_schedule_title(request):
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id') #どの予定表かのIDを取り出す
        new_title = request.POST.get('title') #入力された新しいタイトルを取り出す
        schedule = get_object_or_404(Schedule, id=schedule_id) #該当IDのscheduleがなければ404を返す便利関数
        
        #変更前の旅行開始日・終了日を変数に控えておく
        old_start = schedule.trip_start_date
        old_end = schedule.trip_end_date
        
        #新しい日付（文字列）を取り出す
        new_start_str = request.POST.get('start_date')
        new_end_str = request.POST.get('end_date')
        
        if new_start_str and new_end_str: #どちらも入力されている時だけ変更処理をする
            new_start = datetime.strptime(new_start_str, '%Y-%m-%d').date() #文字列からdate型に変換
            new_end = datetime.strptime(new_end_str, '%Y-%m-%d').date() #文字列からdate型に変換
            #ここでやっとDBに保存できるdate型が出来上がる
            
            #スケジュールの中身を更新、保存
            schedule.title = new_title
            schedule.trip_start_date = new_start
            schedule.trip_end_date = new_end
            schedule.save()
            
            #旅行期間が短くなったかを判定
            shortened = (new_start > old_start) or (new_end < old_end) #new_start > old_startで開始日が後ろにずれた時、new_end < old_endで終了日が手前になった時どちらかが起こっていたら短くなっているとみなしてshortened=True
            if shortened: #短くなった時、期間外のplanを消去する処理を走らせる
                #新しい期間の一日分丸ごとを表すdatetimeを作る（新しい旅行期間の始まり～終わりをdatetimeで表現）
                #datetime.combineはPythonの標準ライブラリにある関数。日付と時刻をくっつけて１つのdatetimeを作る
                start_naive =  datetime.combine(new_start, time.min) #datetime.combineでその日の〇時〇分のdatetimeを作る。minはその日の最初の日時。第１引数→new_start=dateのみ、第２引数→time.min=時刻のみ 合わせるとdatetime型になる
                end_naive = datetime.combine(new_end, time.max) #maxはその日の最後の日時
                #タイムゾーン付（aware）に変える naiveはタイムゾーン情報を持っていない（どこの国の時間か） awareはタイムゾーン付のdatetime
                if timezone.is_naive(start_naive): #もし、start_naiveがnaive（タイムゾーン情報なし）ならそのdatetimeに現在の設定タイムゾーンをくっつけてawareにする
                    new_end_dt = timezone.make_aware(end_naive)
                    new_start_dt = timezone.make_aware(start_naive) if timezone.is_naive(start_naive) else start_naive
                    new_end_dt = timezone.make_aware(end_naive) if timezone.is_naive(end_naive) else end_naive
                
                    #Qオブジェクトで期間外の予定を探す
                    #Plan.objects.filter(schedule=schedule)でこの予定表に紐づくplanだけを対象にする。その上で.filter()の中のQ()をorで繋いでいる
                    plans_to_delete = Plan.objects.filter(schedule=schedule).filter(
                        Q(start_datetime__lt=new_start_dt) | 
                        Q(end_datetime__gt=new_end_dt) | 
                        (Q(end_datetime__isnull=True) & Q(start_datetime__gt=new_end_dt))
                    )
                    #Q(start_datetime__lt=new_start_dt) planの開始時刻が新しい旅行開始日時より前（新しい開始日より前にスタートしている予定）
                    #Q(end_datetime__gt=new_end_dt)　planの終了時刻が新しい旅行終了日時より後（新しい終了日より後に終わる予定）
                    #Q(end_datetime__isnull=True) & Q(start_datetime__gt=new_end_dt) 「終わり時間が設定されていない」かつ「開始時間が新しい旅行終了日時より後」の予定
                    #上記の条件で選択した旅行期間外に飛び出しているplanを全部集めている
                    plans_to_delete.delete() #集めたplans_to_deleteをdelete()で一括削除
        
    return redirect('app:home') #予定表のタイトルや旅行期間の編集が成功した時の遷移画面

#予定表の削除モーダル
@login_required
def delete_schedule(request, schedule_id): #requestはブラウザから送られてきたリクエスト（消去ボタン押されたなどの情報）　schedule_idはURLの中に書かれている予定表ID
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id') #フォームから送られてきたschedule_id（POSTデータ）を使っているが、本来は真下のschedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)だけを使用←Djangoが自動でURLの中にIDが渡される
        schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user) #Scheduleテーブルからidがschedule_idでかつuserがログイン中の人のレコードを探す。見つかればscheduleに入る、見つからなければ404ページを出して処理を止める
        schedule.delete() #取得したscheduleをデータベースから削除する
        return redirect('app:home') #終わったらホーム画面に戻る
    return redirect('app:home')

#予定追加・編集画面
@login_required
def plan_create_or_edit_view(request, schedule_id, plan_id=None): #予定を新規作成と既存予定の編集view　schedule_idでどの予定表の予定か　plan_id=Noneでなしなら新規予定、ありで編集
    schedule = get_object_or_404(Schedule, id=schedule_id) #親の予定表を取得
    plan = get_object_or_404(Plan, id=plan_id)if plan_id else None #編集なら既存plan、新規ならNone　この時点で編集か新規かが確定
    
    selected_day = None

    trip_choices = generate_trip_date_choices(schedule) #旅行期間から日付選択肢を作る 下のdef generate_trip_date_choicesに繋がる
    
    #リンクフォームセットを定義　フォームセット＝planに紐づくリンクを複数扱うための仕組み
    extra_links = 1 #空フォームを最初に1個表示
    #inlineformset_factoryで親（Plan）に紐づく子（Link）をまとめて編集できるフォームセットを作成
    LinkFormSet = inlineformset_factory(
        Plan, #親
        Link, #子（１対多）
        form=LinkForm, #linkモデルの一行分のフォームの形
        formset=BaseLinkFormSet, #カスタムルール　フォームセット全体に独自のルールを足せる
        extra=extra_links,
        max_num=5,
        validate_max=True, #６個以上送られたらエラーにする
        can_delete=True #削除チェックを自動で付ける
    )

    extra_pictures = 1
    PictureFormSet = inlineformset_factory(
        Plan,
        Picture,
        form=PictureForm,
        formset=BasePictureFormSet,
        extra=extra_pictures,
        max_num=6,
        validate_max=True,
        can_delete=True,
    )
    
    if request.method == 'POST':
        form = PlanForm(
            request.POST, #文字データが入っている
            request.FILES, #写真などのファイルが入っている
            instance=plan, #planがNoneの時に新規作成、planが既存オブジェクトの時に上書き保存になる
            trip_dates=trip_choices #旅行期間の日付選択肢をフォームに渡す引数
        )
        
        #同じページにフォームセットが２つあるため、名前が混ざらないようにprefix='links'、'pictures'を指定
        link_formset = LinkFormSet(request.POST or None, request.FILES or None, instance=plan, prefix='links')
        picture_formset = PictureFormSet(request.POST or None, request.FILES or None, instance=plan, prefix='pictures')
        
        #写真フォームセットを１つずつ見て削除なら空扱いにする
        for f in picture_formset:
            delete_flag = f.cleaned_data.get('DELETE', False) if f.is_valid() else False
            if delete_flag:
                f.empty_permitted = True
        
        #どのカテゴリが選ばれたか取る　バリエーションエラーで画面を再表示する時に選択状態を保つ目的    
        selected_category = request.POST.get('action_category') or ''
        
        #plan、link、pictureの３つすべてOKの時だけ保存
        if form.is_valid() and link_formset.is_valid() and picture_formset.is_valid():
            
            plan_instance = form.save(commit=False) #commit=FalseでDBに保存しないでオブジェクトだけ作る　plan_instance.schedule = scheduleを入れたいから（planモデルをscheduleと紐づけしてから保存したいから）
            plan_instance.schedule = schedule #planモデルをscheduleと紐づけ
            plan_instance.save()
            
            #予定表画面（ホーム画面）で更新順に並び替えできるように、予定が更新された＝予定表も更新されたと印をつける
            schedule.updated_at = timezone.now()
            schedule.save(update_fields=['updated_at']) #updated_atだけを更新（他のフィールド触らない）
            
            #写真フォームセットを１つずつ処理
            for picture_form in picture_formset: #picture_formでフォームセットの中の1枚分のフォーム
                instance = picture_form.instance #instanceはそのフォームが紐づくpictureモデルの実体（DBの1行）　既存画像ならinstance.pkがある（DBに存在）　新規ならinstance.pkがない
                delete_flag = picture_form.cleaned_data.get('DELETE', False) #そのフォームで削除にチェック入ったか
                image = picture_form.cleaned_data.get('image') #新しくアップロードされた画像ファイルが入っているか
                
                #新規で何もしていない空フォームは無視する
                #削除チェックなし、画像も選ばれてない、DBにも存在しない→（continue）ただの空フォームだから保存しないで次へ
                if not delete_flag and not image and not instance.pk:
                    continue
                
                #既存画像に削除チェックが入っていたら削除
                if delete_flag and instance.pk:
                    instance.delete()
                    continue
                #削除じゃない場合は保存する（新規or既存更新）
                if not delete_flag:
                    picture = picture_form.save(commit=False) #save(commit=False)で一旦DBに保存せずにpictureオブジェクトだけ作る
                    picture.plan = plan_instance #その画像をどの予定の画像か紐づける（FKセット）
                    picture.save() #DBに保存
        
            #保存後に何日目を表示するかを決める
            if plan_instance.start_datetime:
                trip_start = schedule.trip_start_date #旅行の開始日（例：8/1）
                saved_date = localtime(plan_instance.start_datetime).date() #保存した予定の開始日（例：8/3）
                selected_day = (saved_date - trip_start).days + 1 #（例：8/3－8/1＝2日差　そこに＋1して3日目を表示する）
            else:
                selected_day = 1 #start_datetimeが未入力なら1日目を表示
                    
            #リンクフォームセットを保存するが一旦DBには保存しない（リンクの保存時に追加処理をしたいため）
            link_instances = link_formset.save(commit=False)
            
            #フォームセットでcan_delete=Trueにしているため、削除チェックが入ったリンクはdeleted_objectsに入る
            for obj in link_formset.deleted_objects:
                obj.delete()
                
            #削除チェックはないが、URLが空になった既存データを消す
            for form in link_formset:
                if form.instance.pk:
                    url_value = form.cleaned_data.get('url') if form.is_valid() else form.data.get(form.add_prefix('url')) #通常のURLとバリエーション失敗時でも値を拾えるように
                    if not url_value: #URL空の時
                        form.instance.delete()
                
            #新規と更新のリンクを保存（空欄は保存しない）
            for link in link_instances:
                if link.url and link.url.strip(): #URLが空じゃないものだけ保存（スペースだけも弾く）
                    link.plan = plan_instance #どの予定のリンクかFKで紐づける
                    link.action_category = plan_instance.action_category #リンク側にもカテゴリを持たせているなら同期
                    link.save() #DBに保存
                
            #保存が終わったら詳細画面に戻す　reverseでschedule/<id>/みたいなURL文字列を作る＋selected_day=3のようなクエリをつける
            return redirect(reverse('app:schedule_detail', args=[schedule_id]) + f'?selected_day={selected_day}')
            
        else: #バリエーションエラー後の再表示
            #テンプレートに渡す移動手段の一覧データ　DBのTransportationMethodを全部取ってテンプレートで使いやすい形に辞書型を使って整形
            tm = [] #tmの中のイメージ[{'id':1, 'label': 'walk', 'icon': 'fa-person-walking'},{・・・},]
            for m in TransportationMethod.objects.all():
                tm.append({
                    'id': m.id,
                    'label': m.transportation,
                    'icon': m.transportation_icon_class,
                })
                
            #画面に渡すcontextを揃える
            return render(request, 'app/plan_form.html', {
                'form': form, #Plan本体のフォーム（カテゴリ、日付、メモなど）
                'link_formset': link_formset, #URL欄
                'picture_formset': picture_formset, #写真欄
                'schedule': schedule, #どの予定表に紐づく予定か
                'form_title': '予定編集' if plan else '予定追加', #画面タイトル文字
                'schedule_id': schedule_id, #どの予定表に紐づく予定か
                'transportation_methods': tm, #移動手段の選択肢一覧
                'selected_category': selected_category, #カテゴリの初期選択に使う
                'plan': plan, #編集なら既存plan、追加ならNone
            })
    else: #GETの時（編集・新規）
        selected_category = plan.action_category if plan else '' #編集ならplan.action_category（移動、観光など）を入れる、新規なら空文字
        if plan: #planありの時（編集画面）
            initial = {} #DBには日時がまとまった状態で保存しているが、フォームでは日にちと時間を分けているので、分解してフォームに渡すためinitialを作成
            if plan.start_datetime: #start_datetimeがあるかチェック→あれば日にちと時間に分解
                local_start = localtime(plan.start_datetime) #日本時間に直す
                #date()とtime()に分解してinitialに入れる
                initial['start_date'] = local_start.date()
                initial['start_time'] = local_start.time()
            if plan.end_datetime: #end_datetimeがあるかチェック→あれば日にちと時間に分解
                local_end = localtime(plan.end_datetime)
                #date()とtime()に分解してinitialに入れる
                initial['end_date'] = local_end.date()
                initial['end_time'] = local_end.time()
                
            form = PlanForm(instance=plan, trip_dates=trip_choices, initial=initial) #instance=planでplan既存データでフォーム作る（編集用）、trip_dates=trip_choicesで旅行期間の日付セレクトの選択肢を渡す、initial=initialでさっき分解したdateとtimeを初期値に入れる
            
            #GET時のlink_formsetも作成　None：DBの値表示　request.POSTでPOSTエラー時の入力途中の値を表示
            link_formset = LinkFormSet(
                request.POST or None,
                request.FILES or None,
                instance=plan,
                prefix='links', #picture_formsetと混ざらないように識別子を指定
            )
            
            picture_formset = PictureFormSet(instance=plan, prefix='pictures')
        else: #planなしの時（新規画面）
            #GETパラメータから日付を取り出す（文字列で）　予定詳細画面からこの日の予定追加を押した時に渡す
            date_str = request.GET.get('date') or request.GET.get('start') #URLのdate=．．．やstart=．．．みたいなクエリパラメータから日付文字列をもらう処理
            end_str = request.GET.get('end')
            
            start_date = parse_date(date_str) if date_str else None #date_strが無ければNone　parse_date()で文字列から日付型に変換
            end_date = parse_date(end_str) if end_str else start_date #end_strが無ければstart_datenにする
            
            #フォームの初期値にする
            initial = {} #initialはフォームの初期入力値を入れるための辞書型　例）新規追加画面を開く→開始日が選ばれている状態、終了日も同じ日で入っている状態にしたいからinitialを用意している
            if start_date:
                initial['start_date'] = start_date
            if end_date:
                initial['end_date'] = end_date
                
            form = PlanForm(trip_dates=trip_choices, initial=initial) #plan本体のフォーム　trip_dates=trip_choicesで旅行期間の候補（セレクトボックス）をフォームに渡す　initial=initialでさっき作った開始日などフォームにいれる
            link_formset = LinkFormSet(request.POST or None, request.FILES or None, instance=plan, prefix='links')
            picture_formset = PictureFormSet(instance=plan, prefix='pictures')
            
        #POST時と同様にテンプレートに渡す移動手段の一覧データ　DBのTransportationMethodを全部取ってテンプレートで使いやすい形に辞書型を使って整形
        tm = []
        for m in TransportationMethod.objects.all():
            tm.append({
                'id': m.id,
                'label': m.transportation,
                'icon': m.transportation_icon_class,
            })
            
        #POST時と同様に画面に渡すcontextを揃える
        return render(request, 'app/plan_form.html', {
            'form': form, 
            'link_formset': link_formset,
            'picture_formset': picture_formset,
            'schedule': schedule,
            'form_title': '予定編集' if plan else '予定追加',
            'schedule_id': schedule_id,
            'transportation_methods': tm,
            'selected_category': selected_category,
            'plan': plan,
        })
    
#旅行期間（開始日～終了日）をもとに、1日ずつの日付リストを作る関数
def generate_trip_date_choices(schedule): #scheduleはscheduleモデルの１件
    start = schedule.trip_start_date #date型として開始日を取り出す
    end = schedule.trip_end_date #date型として終了日を取り出す
    delta = (end - start).days #end - startで期間オブジェクト　.daysで何日分か　例）delta = 3で表す
    
    #日付リストを作ってreturn
    return [start + timedelta(days=i) for i in range(delta + 1)] #start + timedelta(days=i)はtimedelta(days=0)＝開始日　delta + 1をしないと最終日が抜けてしまう

#予定詳細画面
#予定表の詳細画面に表示するためにplanを日付ごとに並び替えてテンプレートに渡す処理
@login_required
def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user) #scheduleを1件取得
    #取得したscheduleに紐づくplanを全部取得（リンク、写真も一緒に）
    plans = Plan.objects.filter(schedule_id=schedule_id,).prefetch_related(
        Prefetch('links'),
        Prefetch('pictures'),
    ).order_by('start_datetime')

    #日付ごとの入れもの作る　例）2025-12-1: [paln1, plan2],
    plans_by_date = defaultdict(list)
    
    #planを１つずつ見て、どの日付に入れるか決める
    for plan in plans:
        if not plan.start_datetime or not plan.end_datetime:
            continue
        
        #日付ごとに表示するため、datetimeをdateに変換
        start_date = localtime(plan.start_datetime).date()
        end_date = localtime(plan.end_datetime).date()
        
        #宿泊カテゴリだけチェックインとアウトに分ける
        if plan.action_category == 'stay':
            ci = deepcopy(plan) #1件のplanを表示用に２つに分けるため、ci:チェックイン用のコピー、co:チェックアウト用のコピー
            ci.display_type = 'checkin' #テンプレート側で表示を分岐するため
            ci.display_datetime = plan.start_datetime #並び替えや表示用の時刻として使いやすく
            ci.is_stay_display = True #表示用コピー目印
            plans_by_date[start_date].append(ci) #チェックインはstart_dateの日に入れる
            
            co = deepcopy(plan)
            co.display_type = 'checkout'
            co.display_datetime = plan.end_datetime
            co.is_stay_display = True
            plans_by_date[end_date].append(co) #チェックアウトはend_dateの日に入れる
            
        #宿泊カテゴリ以外の予定を処理 開始日～終了日まで、予定を毎日分表示リストのに入れる 2日以上またぐ予定でも各日すべてに表示できる
        else:
            current_date = start_date #開始日をセット
            #日付を1日ずつ進めるwhileループ current_dateがend_dateを超えるまで繰り返す
            while current_date <= end_date:
                plans_by_date[current_date].append(plan) #その日の予定リストにplanを追加 plans_by_dateは日付→その日の予定リストの辞書　例）plans_by_date[12/1] = [paln], plans_by_date[12/2] = [paln]
                current_date += timedelta(days=1) #日付を1日進める
        
        #同じ日に、時間が重なっている予定の処理
        for date, day_plans in plans_by_date.items(): #1日ずつ処理するループ
            sorted_day_plans = sorted(day_plans, key=lambda plan: getattr(plan, 'display_datetime', plan.start_datetime)) #その日の予定を時刻順に並べる

            #重なり判定の準備
            active_ends = [] #今までに表示した予定の終了時刻一覧
            for plan in sorted_day_plans:
                plan.nest_level = 0 #重なっていない前提
                
                if getattr(plan, 'is_stay_display', False): #宿泊カテゴリは重なり判定を除外
                    continue
                
                for end in active_ends: #新しい予定開始と既存予定の終了が被っていたら＋１する
                    if plan.start_datetime < end:
                        plan.nest_level += 1
                active_ends.append(plan.end_datetime) #新しい予定の終了時刻を登録
                
            plans_by_date[date] = sorted_day_plans #その日の予定リストを更新

    #旅行期間の日付リストを作る　開始日～終了日までを1日ずつ並べたリストを作成
    date_list = []
    current_date = schedule.trip_start_date
    while current_date <= schedule.trip_end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    #予定が入っていない日にも空リストを用意　詳細画面で日付がクリックできるようにするため
    for d in date_list:
        if d not in plans_by_date:
            plans_by_date[d] = []
        
    #日付の並び順を確定させる
    sorted_dates = date_list
    
    #移動手段マスタをテンプレート用の形に変換　アイコン表示と移動手段名の表示に使うため
    tm = []
    for m in TransportationMethod.objects.all():
        tm.append({
            'id': m.id,
            'label': m.transportation,
            'icon': m.transportation_icon_class,
        })

    #テンプレートに渡すデータ一式
    context = {
        'schedule_id': schedule.id,
        'plans_by_date': plans_by_date,
        'sorted_dates': sorted_dates,
        'schedule': schedule,
        'transportation_methods': tm,
        'sorted_dates': sorted(plans_by_date.keys()),
    }
    return render(request, 'app/schedule_detail.html', context)

#予定削除モーダル
@login_required
def plan_delete_view(request, plan_id):
    if request.method == 'POST': #POSTの時だけ削除
        #削除対象のplanを取得
        plan = get_object_or_404(Plan, id=plan_id)
        schedule = plan.schedule
        
        #予定に開始時刻がある場合、削除された予定があった日付を表示する処理
        if plan.start_datetime:
            trip_start = schedule.trip_start_date
            deleted_date = localtime(plan.start_datetime).date()
            selected_day = (deleted_date - trip_start).days + 1
        #開始時刻がない場合は1日目を表示
        else:
            selected_day = 1
            
        plan.delete()
        schedule.updated_at = timezone.now() #scheduleの更新日時を更新
        schedule.save(update_fields=['updated_at'])
        
        return redirect(f"{reverse('app:schedule_detail', args=[schedule.id])}?selected_day={selected_day}")
    
# 持ち物一覧画面（CVBバージョン）
# @login_required
# class PackingItemView(ListView):