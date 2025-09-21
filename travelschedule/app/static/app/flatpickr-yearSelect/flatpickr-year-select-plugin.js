function yearSelectPlugin(pluginConfig) {
    return function(fp) {
        var config = Object.assign({
            shorthand:false,
            dateFormat:"Y",
            theme:"light"
        }, pluginConfig);

        return {
            onReady: function() {
                var yearElement = fp.currentYearElement;

                if (yearElement && yearElement.parentNode) {
                    yearElement.parentNode.removeChild(yearElement);
                }

                var select = document.createElement("select");
                select.className = "flatpickr-year-select";

                var thisYear = new Date().getFullYear();
                var startYear = 2023;
                var endYear = thisYear + 5;

                for (var y = startYear; y <= endYear; y++) {
                    var option = document.createElement("option");
                    option.value = y;
                    option.text = y;
                    if (y === fp.currentYear) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                }

                select.addEventListener("change", function() {
                    fp.changeYear(parseInt(this.value, 10));
                });

                fp.monthNav.insertBefore(select, fp.monthNav.childNodes[2]);

                if (config.theme) {
                    fp.calendarContainer.classList.add(config.theme +  "-theme");
                }
            }
        };
    };
}