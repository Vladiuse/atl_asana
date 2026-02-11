class ValentineFormState {
    constructor() {
        this.recipientId = null
        this.imageId = null
        this.text = ""
        this.isAnonymously = true
        this.anonymousSignature = "Инкогнито"
    }

    is_valid() {
        return (
            this.recipientId !== null &&
            this.imageId !== null &&
            this.text.trim() !== ""
        )
    }

    reset() {
        this.recipientId = null
        this.imageId = null
        this.text = ""
        this.isAnonymously = true
        this.anonymousSignature = "Инкогнито"
    }
}

class IconFactory {
    static get arrowNext() {
        const i = document.createElement("i")
        i.classList.add("fa-solid", "fa-angle-right")
        return i
    }

    static get arrowPrev() {
        const i = document.createElement("i")
        i.classList.add("fa-solid", "fa-angle-left")
        return i
    }

    static get delete() {
        const i = document.createElement("i")
        i.classList.add("fa-regular", "fa-trash-can")
        return i
    }

    static get loadHeart() {
        var div = document.createElement("div")
        div.classList.add("heart", "btn-load-heart")
        return div
    }

    static get heartPlus() {
        var div = document.createElement("i")
        div.classList.add("fa-solid", "fa-heart-circle-plus")
        return div
    }

    static get mailClose() {
        var div = document.createElement("i")
        div.classList.add("fa-solid", "fa-envelope")
        return div
    }

    static get mailOpen() {
        var div = document.createElement("i")
        div.classList.add("fa-regular", "fa-envelope-open")
        return div
    }

    static get eye() {
        var div = document.createElement("i")
        div.classList.add("fa-solid", "fa-eye", "view-icon")
        return div
    }
}


class BottomBar {
    constructor() {
        this.elem = document.querySelector("#bottom-block")
        this.button = document.getElementById("next-btn")
        this._clickHandlerFunc = null
        this._disabled = false

        this.__init__()
    }

    __init__() {
        this.button.addEventListener("click", this._clickHandler.bind(this))
    }

    _clickHandler() {
        if (this._clickHandlerFunc) {
            this._clickHandlerFunc()
        }
    }

    set disabled(value) {
        if (typeof value !== "boolean") {
            throw new Error("Disabled value must be boolean")
        }
        this._disabled = value
        this.button.disabled = value
        if (value) {
            this.elem.classList.add("disabled")
        } else {
            this.elem.classList.remove("disabled")
        }
    }

    appendToButton(...elems) {
        if (elems.length == 0) throw new Error("Pass at least one argument to appendToButton method ")
        this.button.innerHTML = ""
        elems.forEach(el => {
            if (el instanceof HTMLElement) {
                this.button.append(el)
            } else if (typeof el === "string") {
                const span = document.createElement("span")
                span.textContent = el
                this.button.append(span)
            } else {
                throw new Error("Invalid element type")
            }
        })
    }

    showLoading(loadingText = "") {
        const children = Array.from(this.button.children)
        children.forEach(elem => { elem.classList.add('d-none') })
        var loadingTextDiv = document.createElement("div")
        loadingTextDiv.innerText = loadingText
        this.button.append(IconFactory.loadHeart, loadingTextDiv)
    }

    hideLoading() {
        const children = Array.from(this.button.children)
        children.forEach(elem => {
            if (elem.classList.contains("d-none")) {
                elem.classList.remove("d-none")
            } else {
                elem.remove()
            }
        })
    }

    setClickHandler(handlerFunc) {
        this._clickHandlerFunc = handlerFunc
    }

    resetEvent() {
        this._clickHandlerFunc = null
    }

    show(...elems) {
        this.appendToButton(...elems)
        this.elem.classList.add('show')
    }

    hide() {
        this.elem.classList.remove('show')
    }

    close({ reset = true } = {}) {
        this.hide()
        if (reset) {
            this.disabled = false
            this.resetEvent()
        }
    }
}

class EmployeeScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("chose-employee")
        this.employeeCardsContainer = this.elem.querySelector(".employee-cards-container")
    }

    _drawCard(employeeData) {
        const card = document.createElement("div")
        card.dataset.employeeId = employeeData.id
        card.className = "employee-card"
        const img = document.createElement("img")
        img.src = employeeData.avatar || this.context.defaults.avatar
        const h3 = document.createElement("h3")
        h3.textContent = employeeData.fullName
        const p = document.createElement("p")
        p.textContent = employeeData.position
        card.append(img, h3, p)
        return card
    }

    _makeEmployeeCardActive(cardElem) {
        var active = this.elem.querySelectorAll(".employee-card.active")
        if (cardElem.classList.contains("active")) {
            cardElem.classList.remove("active")
            this.context.ui.bottomBar.hide()
        } else {
            this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
            active.forEach(card => {
                card.classList.remove("active")
            })
            cardElem.classList.add("active")
        }
    }

    _submitEmployee() {
        var chosenEmployee = this.elem.querySelector(".employee-card.active")
        if (!chosenEmployee) {
            throw Error("No active employee elem")
        }
        if (!chosenEmployee.dataset.employeeId) {
            throw Error("Cant get active employee 'id' from elem")
        }
        this.context.formState.recipientId = Number(chosenEmployee.dataset.employeeId)
        this.context.ui.bottomBar.close()
        this.router.go("form/chose-image")
    }

    async show() {
        this.context.formState.reset()
        this.context.ui.bottomBar.setClickHandler(this._submitEmployee.bind(this))
        var employees = await this.context.collections.employees.getAvailableToSend()
        this.employeeCardsContainer.innerHTML = ""
        employees.forEach(employeeData => {
            var card = this._drawCard(employeeData)
            this.employeeCardsContainer.appendChild(card)
            card.addEventListener("click", this._makeEmployeeCardActive.bind(this, card))
        })
    }

    hide() {
        var chosenEmployee = this.elem.querySelector(".employee-card.active")
        if (chosenEmployee) {
            chosenEmployee.classList.remove("active")
        }

    }
}
class ChoseImageScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("chose-img")
        this.swiperWrapper = this.elem.querySelector(".swiper-wrapper")
        this.swiper = null
        this.loadImgInput = document.getElementById('valentine-image-input')
        this.triggerBtn = document.querySelector('#trigger-upload');
        this.previewImg = document.querySelector('#image-preview');
        this.previewContainer = document.querySelector('#image-preview-container');

        this.__init__()
    }

    __init__() {
        [this.elem.querySelector(".heart-button-next"), this.elem.querySelector(".heart-button-prev")]
            .forEach(btn => {
                btn.addEventListener("click", (e) => {
                    const elem = e.currentTarget
                    elem.classList.remove("swiper-nav-click")
                    void elem.offsetWidth
                    elem.classList.add("swiper-nav-click")
                })
            })


        // 1. Проксируем клик с красивой кнопки на системный инпут
        this.triggerBtn.addEventListener('click', () => this.loadImgInput.click());

        // 2. Обрабатываем выбор файла
        this.loadImgInput.addEventListener('change', (e) => {
            const files = e.target.files;

            if (files && files[0]) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    this.previewImg.src = event.target.result;
                    this.previewContainer.className = "preview-visible";
                    this.triggerBtn.style.display = "none";
                    this.context.ui.bottomBar.show("Load imgs")
                    this.context.ui.bottomBar.setClickHandler(this.handleUpload.bind(this))
                };
                reader.readAsDataURL(files[0]);
            }
        });

        // 3. Удаление выбранного фото
        document.querySelector('#remove-image').addEventListener('click', () => {
            this._clearLoadedImg()
            this.context.ui.bottomBar.hide()
        })
    }

    _clearLoadedImg() {
        this.loadImgInput.value = "";
        this.previewContainer.className = "preview-hidden";
        this.triggerBtn.style.display = "flex";
    }

    async handleUpload() {
        this.context.ui.bottomBar.disabled = true
        this.context.ui.bottomBar.showLoading("Загружаю")
        const file = this.loadImgInput.files[0];
        try {
            const valentineImage = await this.context.collections.valentineImages.uploadValentineImage(file);
            console.log("Картинка загружена:", valentineImage);
            setTimeout(() => {
                this.context.ui.bottomBar.disabled = false
                this.context.ui.bottomBar.hideLoading()
                var slideElem = this._createSlide(valentineImage)
                this._addSlideOfNewImage(slideElem)
                this._clearLoadedImg()
                this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
                this.context.ui.bottomBar.setClickHandler(this._submitImage.bind(this))
            }, 1500)
        } catch (e) {
            console.error("Ошибка загрузки:", e);
        }
    }

    _createSlide(imageData) {
        var div = document.createElement("div")
        div.classList.add("swiper-slide")
        div.dataset.imageId = imageData.id
        var img = document.createElement("img")
        img.src = imageData.image
        div.appendChild(img)
        return div
    }

    _createSwiper(imagesData) {
        if (this.swiper) {
            this.swiper.destroy(true, true)
            this.swiperWrapper.querySelectorAll(".swiper-slide").forEach(slide => {
                if (slide.id != "load-image") {
                    slide.remove()
                }
            })
        }
        imagesData.forEach(imageData => {
            var slide = this._createSlide(imageData)
            this.swiperWrapper.appendChild(slide)
        })
        this.swiper = new Swiper('.swiper-container', {
            loop: true,
            pagination: {
                el: '.swiper-pagination',
                type: 'progressbar',
            },
            navigation: {
                nextEl: '.heart-button-next',
                prevEl: '.heart-button-prev',
            },
            on: {
                slideChange: this._slideChange.bind(this)
            }
        })
    }

    _showLoadImageSlide() {
        this.context.ui.bottomBar.hide()
        this._clearLoadedImg()
    }

    _slideChange() {
        if (this.swiper) {
            const index = this.swiper.activeIndex;
            const activeSlide = this.swiper.slides[index];
            if (activeSlide.id == "load-image") {
                this._showLoadImageSlide()
            } else {
                this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
            }
        }

    }

    _addSlideOfNewImage(slideHtml) {
        const totalSlides = this.swiper.slides.length;
        const targetIndex = totalSlides - 1
        this.swiper.addSlide(targetIndex, slideHtml);
        this.swiper.slideTo(targetIndex, 400);
    }

    _submitImage() {
        var activeSlide = this.swiper.slides[this.swiper.activeIndex]
        var selectedId = activeSlide.dataset.imageId
        this.context.formState.imageId = Number(selectedId)
        this.router.go("form/write-text")
    }

    show() {
        var imagesData = this.context.collections.valentineImages.all()
        this._createSwiper(imagesData)
        this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
        this.context.ui.bottomBar.setClickHandler(this._submitImage.bind(this))
    }

    hide() {
        this.context.ui.bottomBar.close()
    }
}

class WriteTextScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("write-text")
        this.textarea = this.elem.querySelector('#write-text textarea')

        this.__init__()
    }

    __init__() {
        this.textarea.addEventListener('input', (e) => {
            const value = e.target.value.trim()

            if (value.length >= 5) {
                this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
            } else {
                this.context.ui.bottomBar.hide()
            }
        })
    }

    _submitText() {
        this.context.formState.text = this.textarea.value
        this.router.go("form/sending-privacy")
    }

    show() {
        this.textarea.value = ""
        this.context.ui.bottomBar.setClickHandler(this._submitText.bind(this))
    }

    hide() {
        this.context.ui.bottomBar.close()
    }
}

class SendingPrivacyScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("sending-privacy")
        this.senderAvatar = this.elem.querySelector(".sender-avatar")
        this.anonRadio = document.getElementById('modeAnonymous');
        this.publicRadio = document.getElementById('modePublic');
        this.signatureSection = document.getElementById('signatureSection');
        this.signatureInput = document.getElementById('signatureInput');
        this.allRadios = this.elem.querySelectorAll('input[name="senderMode"]');

        this.__init__()
    }

    __init__() {
        this.allRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (this.anonRadio.checked) {
                    this._choseAnon()
                } else {
                    this._chosePersonal()
                }
            });
        });

        this.signatureInput.addEventListener("input", () => {
            if (this._isValidAnonName()) {
                this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
            } else {
                this.context.ui.bottomBar.hide()
            }
        });
    }

    _isValidAnonName() {
        const value = this.signatureInput.value.trim();
        const length = value.length;
        return length >= 3
    }

    _choseAnon() {
        this.anonRadio.checked = true;
        this.signatureSection.className = "signature-visible"
        if (this._isValidAnonName()) {
            this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
        } else {
            this.context.ui.bottomBar.hide()
        }
    }
    _chosePersonal() {
        this.publicRadio.checked = true;
        this.signatureSection.className = "signature-hidden"
        this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
    }

    async _submitPrivacy() {
        if (this.publicRadio.checked) {
            this.context.formState.isAnonymously = false
        } else {
            this.context.formState.isAnonymously = true
            this.context.formState.anonymousSignature = this.signatureInput.value
        }
        this.router.go("form/check")
    }

    show() {
        this.senderAvatar.src = this.context.collections.employees.currentEmployee().avatar
        this.context.ui.bottomBar.show("Далее", IconFactory.arrowNext)
        this._chosePersonal()
        this.signatureInput.value = ""
        this.context.ui.bottomBar.setClickHandler(this._submitPrivacy.bind(this))
    }

    hide() {
        this.signatureInput.value = ""
        this.context.ui.bottomBar.close()
    }
}

class CheckFormScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("check-form")
        this.imgElem = document.getElementById("check-img")
        this.textElem = document.getElementById("check-text")
        this.recipientNameElem = document.getElementById("check-recipient-name")
        this.recipientAvatarElem = document.getElementById("check-recipient-avatar")
        this.senderNameElem = this.elem.querySelector(".sender-name")
    }

    _displayData() {
        var imgData = this.context.collections.valentineImages.getById(this.context.formState.imageId)
        var recipientData = this.context.collections.employees.getById(this.context.formState.recipientId)
        var text = this.context.formState.text
        this.imgElem.src = imgData.image
        this.textElem.innerText = text
        this.recipientNameElem.innerText = recipientData.fullName
        this.recipientAvatarElem.src = recipientData.avatar ?? this.context.defaults.avatar
        var senderName = this.context.formState.isAnonymously ? `анонимно от ${this.context.formState.anonymousSignature}` : `от Вашего имени`
        this.senderNameElem.innerText = senderName
    }

    async _submitCheck() {
        this.context.ui.bottomBar.disabled = true
        this.context.ui.bottomBar.showLoading("Сохраняю")
        await this.context.collections.my_valentines.create(this.context.formState)
        setTimeout(() => {
            this.router.go("my-valentines-list", { "show_create_bnt": true })
        }, 2500)
    }

    show() {
        this._displayData()
        this.context.ui.bottomBar.show("Направить стрелу любви", IconFactory.arrowNext)
        this.context.ui.bottomBar.setClickHandler(this._submitCheck.bind(this))
    }

    hide() {
        this.context.ui.bottomBar.close()
    }
}

class MyValentineDetailScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("my-valentine-detail")
        this.valentineTextElem = this.elem.querySelector(".valentine-text")
        this.valentineImgElem = this.elem.querySelector(".valentine-img")
        this.valentineRecipientNameElem = this.elem.querySelector(".valentine-recipient-name")
        this.valentineSenderNameElem = this.elem.querySelector(".valentine-sender-name")
    }

    show({ valentineId } = {}) {
        var valentine = this.context.collections.my_valentines.getById(valentineId)
        var recipient = this.context.collections.employees.getById(valentine.recipientId)
        var valentineImage = this.context.collections.valentineImages.getById(valentine.imageId)
        this.valentineTextElem.innerText = valentine.text
        this.valentineImgElem.src = valentineImage.image
        this.valentineRecipientNameElem.innerText = recipient.fullName
        this.valentineSenderNameElem.innerText = valentine.isAnonymously ? `анонимно от ${valentine.anonymousSignature}` : `от Вашего имени`
    }
}

class MyValentineDeleteScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("my-valentine-delete")
    }

    show({ valentineId } = {}) {
        this.context.ui.bottomBar.show("Удалить", IconFactory.delete)
        this.context.ui.bottomBar.setClickHandler(() => {
            this._submitDelete(valentineId)
        })
    }

    async _submitDelete(valentineId) {
        this.context.ui.bottomBar.showLoading("Удаляю")
        this.context.ui.bottomBar.disabled = true
        await this.context.collections.my_valentines.delete(valentineId)
        setTimeout(() => {
            this.router.go("my-valentines-list")
        }, 2500)
    }

    hide() {
        this.context.ui.bottomBar.close()
    }
}

class MyValentineListScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("my-valentines")
        this.valentineContainer = this.elem.querySelector(".valentine-list")
        this.closeBtn = this.elem.querySelector("[data-screen-close]")
        this.detailButton = this.elem.querySelectorAll(".my-valentine-detail")
        this.deleteButton = this.elem.querySelectorAll(".my-valentine-delete")
    }

    _createValentineItem(valentine) {  // Valentine class
        var recipient = this.context.collections.employees.getById(valentine.recipientId)
        const li = document.createElement("li")
        li.dataset.myValentineId = valentine.id
        li.className = "valentine-item"
        const img = document.createElement("img")
        img.className = "avatar"
        img.src = recipient.avatar || this.context.defaults.avatar
        img.alt = "Avatar"
        const name = document.createElement("span")
        name.className = "name"
        name.textContent = recipient.fullName
        const viewIcon = document.createElement("i")
        viewIcon.className = "fa-solid fa-eye view-icon my-valentine-detail"
        viewIcon.addEventListener("click", () => this.router.go("my-valentines-detail", { valentineId: valentine.id }))
        const deleteIcon = document.createElement("i")
        deleteIcon.className = "fa-solid fa-trash my-valentine-delete"
        deleteIcon.addEventListener("click", () => this.router.go("my-valentines-delete", { valentineId: valentine.id }))
        li.append(img, name, viewIcon, deleteIcon)
        return li
    }

    show(params) {
        this.valentineContainer.innerHTML = ""
        var valentinesData = this.context.collections.my_valentines.all()
        if (valentinesData.length == 0) {
            var block = document.createElement("h3")
            block.innerText = "У вас пока нет созданных валентинок"
            this.valentineContainer.append(block)
        } else {
            this.context.collections.my_valentines.all().forEach(valentineData => {
                var elem = this._createValentineItem(valentineData)
                this.valentineContainer.append(elem)
            })
        }

        if (params.show_create_bnt) {
            this.context.ui.bottomBar.show("Отправить еще", IconFactory.heartPlus)
            this.context.ui.bottomBar.setClickHandler(() => this.router.go("form/chose-employee"))
        }
    }

    hide() {
        this.context.ui.bottomBar.close()
    }
}
class ReceivedValentineDetailScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("received-valentines-detail")
        this.valentineTextElem = this.elem.querySelector(".valentine-text")
        this.valentineImgElem = this.elem.querySelector(".valentine-img")
        this.valentineRecipientNameElem = this.elem.querySelector(".valentine-recipient-name")
        this.valentineRecipientImgElem = this.elem.querySelector(".avatar")
    }

    show({ valentineId } = {}) {
        var valentine = this.context.collections.received_valentines.getById(valentineId)
        var sender = this.context.collections.employees.getById(valentine.senderId)
        this.context.collections.received_valentines.markAsRead(valentineId)
        var valentineImage = this.context.collections.valentineImages.getById(valentine.imageId)
        this.valentineTextElem.innerText = valentine.text
        this.valentineImgElem.src = valentineImage.image
        this.valentineRecipientNameElem.innerText = valentine.isAnonymously ? valentine.anonymousSignature : sender.fullName
        this.valentineRecipientImgElem.src = valentine.isAnonymously ? this.context.defaults.avatar : sender.avatar
    }
}

class ReceivedValentineListScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("received-valentines")
        this.container = this.elem.querySelector(".valentine-list")
        this.waitBlock = this.elem.querySelector(".wait")
        this.noItemsBlock = this.elem.querySelector(".empty")
    }

    _createCards(valentine) {
        var sender = this.context.collections.employees.getById(valentine.senderId)
        const li = document.createElement("li")
        li.dataset.valentineId = valentine.id
        li.className = "valentine-item"
        const img = document.createElement("img")
        img.className = "avatar"
        img.src = valentine.isAnonymously ? this.context.defaults.avatar : sender.avatar
        img.alt = "Avatar"
        const span = document.createElement("span")
        span.className = "name"
        span.textContent = valentine.isAnonymously ? valentine.anonymousSignature : sender.fullName
        var iconsDiv = document.createElement("div")
        iconsDiv.className = "icons"
        var mailIcon = valentine.isReadByRecipient ? IconFactory.mailOpen : IconFactory.mailClose
        iconsDiv.append(mailIcon, IconFactory.eye)
        li.append(img, span, iconsDiv)
        return li
    }

    async show() {
        await this.context.collections.received_valentines.loadAll()
        this.container.innerHTML = ""
        if (!this.context.collections.received_valentines.isUpTime) {
            this.waitBlock.style.display = "block"
            this.noItemsBlock.style.display = "none"
            return
        }
        this.waitBlock.style.display = "none"
        var valentines = this.context.collections.received_valentines.all()
        if (valentines.length == 0) {
            this.noItemsBlock.style.display = "block"
            return
        }
        this.noItemsBlock.style.display = "none"
        valentines.forEach(valentine => {
            var card = this._createCards(valentine)
            card.addEventListener("click", () =>
                this.router.go("received-valentines-detail", { valentineId: valentine.id })
            )
            this.container.append(card)
        })
    }
}

class MainScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("main-screen")
        this.startButton = document.getElementById("start-button")
        this.openMyValentinesButton = document.getElementById("open-my-valentines")

        this.startButton.addEventListener("click", () => {
            this.router.go("form/chose-employee")
        })
        this.openMyValentinesButton.addEventListener("click", () => {
            this.router.go("my-valentines-list")
        })
    }

    show() {
        this.context.ui.bottomBar.close()
    }
}

class PreLoadScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("pre-load-screen")
    }
}


class AboutScreen {
    constructor(router, context) {
        this.router = router
        this.context = context
        this.elem = document.getElementById("about")
    }
}

class ErrorMessageScreen {
    constructor(router) {
        this.router = router
        this.elem = document.getElementById("error-screen")
        this.messageBlock = document.getElementById("error-message")
        this.closeElem = this.elem.querySelector("[data-screen-go]")
    }

    show({ message = "", showCloseButton = false }) {
        if (!message) {
            throw new Error
        }
        if (showCloseButton) {
            this.closeElem.style.display = "block"
        } else {
            this.closeElem.style.display = "none"
        }
        this.messageBlock.innerText = message
    }
}

class ScreenRouter {
    SCREEN_FADE_TIME = 400
    constructor() {
        this.routes = new Map()
        this.currentScreen = null

        this._initGlobalNavigation()
    }

    _initGlobalNavigation() {
        document.querySelectorAll("[data-screen-go]").forEach((elem) => {
            elem.addEventListener("click", (e) => {
                var screen = e.currentTarget.dataset.screenGo
                this.go(screen)
            })
        })
    }

    register(route, screen) {
        if (this.routes.has(route)) {
            throw new Error(`ScreenRouter: route "${route}" already registered`)
        }
        if (!route || typeof route !== "string") {
            throw new Error("ScreenRouter.register: route must be string")
        }
        if (!screen || !(screen.elem instanceof HTMLElement)) {
            throw new Error(`ScreenRouter.register: screen elem for"${route}" must be HTMLElement`)
        }
        this.routes.set(route, screen)
    }

    go(route, params = {}) {
        const screen = this.routes.get(route)
        if (!screen) {
            throw new Error(`ScreenRouter.go: route "${route}" is not registered`)
        }
        if (this.currentScreen != null && typeof this.currentScreen.hide === "function") {
            this.currentScreen.hide()
        }
        if (this.currentScreen) {
            $(this.currentScreen.elem).fadeOut(this.SCREEN_FADE_TIME, () => {
                if (typeof screen.show == "function") {
                    screen.show(params)
                }
                $(screen.elem).fadeIn(this.SCREEN_FADE_TIME)
            })
        } else {
            if (typeof screen.show == "function") {
                screen.show(params)
            }
            $(screen.elem).fadeIn(this.SCREEN_FADE_TIME)
        }
        this.currentScreen = screen
    }
}

class ValentineApp {
    constructor(context, router, telegramApp) {
        this.context = context
        this.router = router
        this.telegramApp = telegramApp
    }

    async start() {
        this.router.go("preload")
        try {
            var tg_user_id = this.telegramApp.initDataUnsafe.user.id
        } catch (error) {
            console.error("Ошибка доступа к данным Telegram:", error.message);
            var tg_user_id = "test_id"
        }

        try {
            var data = await this.context.api.client.getToken(tg_user_id)
            var token = data.token
            this.context.api.client.employeeId = data.employee_id
            this.context.api.client.userId = data.user_id
        } catch (e) {
            console.error("Cant get token", e.message);
            this.router.go("error-screen", { message: `Cant get token, unknown telegram id.\ntelegram_user_id: ${tg_user_id}` })
            return
        }
        console.log(token, "token")
        this.context.api.client.token = token
        this.context.collections.employees.loadAll()
        this.context.collections.valentineImages.loadAll()
        this.context.collections.my_valentines.loadAll()
        this.context.collections.received_valentines.loadAll()
        setTimeout(() => {
            // this.router.go("main")
            this.router.go("form/chose-image")
        }, 28)
    }
}


class ApiClient {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl
        this.token = token
        this.employeeId = null
        this.userId = null
    }

    async employeeList() {
        var url = `${this.baseUrl}/employee/`
        var response = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${this.token}`
            },
        })
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`)
        }
        return await response.json()
    }

    async markValentineRead(valentineId) {
        const url = `${this.baseUrl}/my-valentines/${valentineId}/mark-read/`
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${this.token}`
            }
        })

        if (!response.ok) {
            const errorText = await response.text()
            throw new Error(`HTTP ${response.status}: ${errorText}`)
        }

        return await response.json()
    }

    async valentineList() {
        const url = `${this.baseUrl}/my-valentines/`
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${this.token}`
            },
        })
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`)
        }
        return await response.json()
    }

    async createValentine(payload) {
        const url = `${this.baseUrl}/my-valentines/`
        console.log(payload)
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${this.token}`
            },
            body: JSON.stringify(payload)
        })
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`)
        }
        return await response.json()
    }

    async deleteValentine(valentineId) {
        const url = `${this.baseUrl}/my-valentines/${valentineId}/`
        const response = await fetch(url, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${this.token}`,
            },
        })

        if (!response.ok) {
            const errorText = await response.text()
            throw new Error(`HTTP ${response.status}: ${errorText}`)
        }

        return true
    }

    async valentineImageList() {
        const url = `${this.baseUrl}/my-images/`
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${this.token}`
            },
        })
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`)
        }
        return await response.json()
    }

    async getToken(telegramUserId) {
        const params = new URLSearchParams({
            telegram_user_id: telegramUserId,
        })
        const url = `${this.baseUrl}/get-token/?${params.toString()}`
        const response = await fetch(url, {
            method: "GET",
        })
        if (!response.ok) {
            const errorText = await response.text()
            throw new Error(`HTTP ${response.status}: ${errorText}`)
        }
        const responseData = await response.json()
        // responseData = {
        //     "token": token.key,
        //     "employee_id": employee.pk,
        //     "user_id": employee.user.pk,
        // }
        return responseData
    }

    async receivedValentines() {
        const url = `${this.baseUrl}/my-valentines/received/`
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${this.token}`,
            },
        })

        if (!response.ok) {
            const text = await response.text()
            throw new Error(`HTTP ${response.status}: ${text}`)
        }

        return await response.json()
    }

    async uploadValentineImage(imageFile, ownerId) {
        const url = `${this.baseUrl}/load-valentine-image/`;

        // Для отправки файлов используем FormData
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('owner_id', ownerId);

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": CSRF_TOKEN,
                // ВАЖНО: Content-Type НЕ ПИШЕМ, браузер поставит его сам с boundary
            },
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        return await response.json();
    }
}

class Employee {
    constructor(data) {
        this.id = data.id
        this.name = data.name
        this.surname = data.surname
        this.position = data.position
        this.avatar = data.avatar
    }

    get fullName() {
        return `${this.name} ${this.surname}`
    }
}

class EmployeeCollection {
    constructor(apiClient, context) {
        this.context = context
        this.apiClient = apiClient
        this.items = new Map()
        this.availableToSend = []
    }

    async loadAll() {
        const data = await this.apiClient.employeeList()
        this.items.clear()
        data.forEach(emp => this.items.set(emp.id, new Employee(emp)))
    }

    getById(id) {
        const employee = this.items.get(id)
        if (!employee) {
            throw new Error(`Employee with id ${id} not found in collection`)
        }
        return employee
    }

    getAvailableToSend() {
        const usedRecipientIds = new Set(
            this.context.collections.my_valentines
                .all()
                .map(v => v.recipientId)
        )
        return Array.from(this.items.values())
            .filter(emp => {
                const isNotSent = !usedRecipientIds.has(emp.id);
                const isNotMe = emp.id !== this.apiClient.employeeId;
                return isNotSent && isNotMe;
            });
    }

    all() {
        return Array.from(this.items.values())
    }

    currentEmployee() {
        return this.getById(this.apiClient.employeeId)
    }
}

class Valentine {
    constructor(data) {
        this.id = data.id
        this.senderId = data.sender
        this.recipientId = data.recipient
        this.imageId = data.image
        this.text = data.text
        this.isAnonymously = data.is_anonymously
        this.anonymousSignature = data.anonymous_signature
        this.created = new Date(data.created)
        this.isReadByRecipient = data.is_read_by_recipient
    }
}

class MyValentineCollection {
    constructor(apiClient, context) {
        this.context = context
        this.apiClient = apiClient
        this.items = new Map()
        this.isUpTime = false
        this.received = new Map()
    }

    add(valentineData) {
        const valentine = new Valentine(valentineData)
        this.items.set(valentine.id, valentine)
        return valentine
    }

    async create(formState) {
        const payload = {
            recipient: formState.recipientId,
            image: formState.imageId,
            text: formState.text,
            is_anonymously: formState.isAnonymously,
            anonymous_signature: formState.anonymousSignature,
        }

        const data = await this.apiClient.createValentine(payload)
        const valentine = new Valentine(data)
        this.items.set(valentine.id, valentine)
        return valentine
    }

    async delete(valentineId) {
        if (!this.items.has(valentineId)) {
            throw new Error(`Valentine with id ${valentineId} not found in collection`)
        }
        await this.apiClient.deleteValentine(valentineId)
        this.items.delete(valentineId)
    }

    async loadAll() {
        const data = await this.apiClient.valentineList()
        this.items.clear()
        data.forEach(valentineData => this.items.set(valentineData.id, new Valentine(valentineData)))
    }

    getById(id) {
        const valentine = this.items.get(id)
        if (!valentine) {
            throw new Error(`Valentine with id ${id} not found in collection`)
        }
        return valentine
    }

    all() {
        return Array.from(this.items.values())
    }
}

class ReceivedValentineCollection {
    constructor(apiClient, context) {
        this.context = context
        this.apiClient = apiClient
        this.items = new Map()
        this.isUpTime = false
    }

    async loadAll() {
        const data = await this.apiClient.receivedValentines()
        this.items.clear()
        this.isUpTime = data.is_up_time
        data.valentines.forEach(v => {
            this.items.set(v.id, new Valentine(v))
        })
    }

    all() {
        return Array.from(this.items.values())
    }

    async markAsRead(valentineId) {
        if (!this.items.has(valentineId)) {
            throw new Error(`Valentine with id ${valentineId} not found in collection`)
        }
        await this.apiClient.markValentineRead(valentineId)
        const valentine = this.items.get(valentineId)
        valentine.isReadByRecipient = true
        return valentine
    }

    getById(id) {
        const valentine = this.items.get(id)
        if (!valentine) {
            throw new Error(`Valentine with id ${id} not found in collection`)
        }
        return valentine
    }
}

class ValentineImage {
    constructor(data) {
        this.id = data.id
        this.image = data.image
        this.owner = data.owner
    }
}

class ValentineImageCollection {
    constructor(apiClient, context) {
        this.context = context
        this.apiClient = apiClient
        this.items = new Map()
    }

    async loadAll() {
        const data = await this.apiClient.valentineImageList()
        this.items.clear()
        data.forEach(imgData => {
            this.items.set(imgData.id, new ValentineImage(imgData))
        })
    }

    getById(id) {
        const image = this.items.get(id)
        if (!image) {
            throw new Error(`ValentineImage with id ${id} not found`)
        }
        return image
    }

    add(valentineImageData) {
        const valentine = new ValentineImage(valentineImageData)
        this.items.set(valentine.id, valentine)
        return valentine
    }

    all() {
        return Array.from(this.items.values())
    }

    async uploadValentineImage(file) {
        var data = await this.apiClient.uploadValentineImage(file, this.apiClient.userId);
        var valentineImage = this.add(data)
        return valentineImage
    }

}