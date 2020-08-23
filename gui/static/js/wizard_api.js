window.wizard = {
    pageId: 0,
    pageSum: 0,

    init: function (pageEnter = 0, bindPrev=true, bindNext=true) {
        wizard.pageSum = 0;

        while (true) {
            if (!document.getElementById("wizard-pg-" + this.pageSum)) {
                break;
            }
            wizard.pageSum++;
        }

        for (let i = 0; i < wizard.pageSum; i++) {
            $("#wizard-pg-" + i).hide();
        }
        $("#wizard-pg-" + pageEnter).show();
        wizard.pageId = pageEnter

        if (bindPrev)
            $("#wizard-prev").click(function () {
                wizard.fadePrev()
            });
        if (bindNext)
            $("#wizard-next").click(function () {
                wizard.fadeNext()
            });

        wizard.updateBtnState();
    },

    updateBtnState: function () {
        if (wizard.pageId === 0) {
            $("#wizard-prev").addClass("disabled");
            $("#wizard-skip").removeClass("disabled");
        } else {
            $("#wizard-prev").removeClass("disabled");
            $("#wizard-skip").addClass("disabled");
        }

        if (wizard.pageId === wizard.pageSum - 1) {
            $("#wizard-next").hide();
            $("#wizard-finish").show();
        } else {
            $("#wizard-next").show();
            $("#wizard-finish").hide();
        }
    },

    toPage: function (pageEnter) {
        $("#wizard-pg-" + wizard.pageId).hide();
        $("#wizard-pg-" + pageEnter).show();
        wizard.pageId = pageEnter;
        wizard.updateBtnState();
    },

    fadeToPage: function (pageEnter, speed = "normal") {
        $("#wizard-pg-" + wizard.pageId).fadeOut(speed, function () {
            $("#wizard-pg-" + pageEnter).fadeIn(speed);
            wizard.pageId = pageEnter;
            wizard.updateBtnState();
        });
    },

    slideToPage: function (pageEnter, speed = "normal") {
        $("#wizard-pg-" + wizard.pageId).slideUp(speed, function () {
            $("#wizard-pg-" + pageEnter).slideDown(speed);
            wizard.pageId = pageEnter;
            wizard.updateBtnState();
        });
    },

    fadePrev: function () {
        if (wizard.pageId !== 0) {
            wizard.fadeToPage(wizard.pageId - 1);
        }
    },

    fadeNext: function () {
        if (wizard.pageId !== wizard.pageSum - 1) {
            wizard.fadeToPage(wizard.pageId + 1);
        }
    }
}