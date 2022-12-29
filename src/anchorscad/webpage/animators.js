

// Constructor for timed sample values.
class TimedSampleValue {
    constructor(value, timestampMillis) {
        this.value = value;
        this.timestampMillis = timestampMillis;
    }
}

class TimedSampleClientXEvent extends TimedSampleValue {
    constructor(event) {
        super(event.clientX, Date.now());
    }
}

// Constructor for SpeedDeterminator object.
// The speed determinator is used to determine the speed of the
// mouse pointer in pixels since some given time in the past.
class SpeedDeterminator {
    constructor(spanMillis) {
        this.spanMillis = spanMillis;
        this.samples = [];
    }

    // Adds a new sample value.
    addSample(sampleValue) {
        // If the latest sample has the same timestamp, replace it.
        if (this.samples.length > 0) {
            const latestSample = this.samples[this.samples.length - 1];
            if (latestSample.timestampMillis >= sampleValue.timestampMillis) {
                this.samples[this.samples.length - 1] = sampleValue;
                return;
            }
        }
        this.samples.push(sampleValue);
        this.removeOldSamples(sampleValue.timestampMillis);
    }

    // Removes samples older than this.spanMillis.
    removeOldSamples(toMillis) {
        // Keep at least 2 samples, even if it is older than the spanMillis.
        while (this.samples.length > 2) {
            const sample = this.samples[0];
            if (toMillis - sample.timestampMillis < this.spanMillis) {
                break;
            }
            this.samples.shift();
        }
    }

    // Returns the speed in pixels per millisecond.
    getSpeed = function () {
        if (this.samples.length < 2) {
            return 0;
        }
        const sampleA = this.samples[0];
        const sampleB = this.samples[this.samples.length - 1];
        const elapsedMillis = sampleB.timestampMillis - sampleA.timestampMillis;
        if (elapsedMillis <= 0) {
            return 0;
        }
        const distance = sampleB.value - sampleA.value;
        return distance / elapsedMillis;
    }
}

const SPEED_SAMPLE_SPAN_MILLIS = 100;
const MIN_SPEED_FOR_INTERIA_PX_PER_SEC = 10;
const INERTIA_ANIMATION_DURATION_MILLIS = 500;
const MIN_PX_FOR_CLICK_EVENT = 5;

const MAX_ELASTIC_WIDTH = 200;

// Constructor function for a scrolling object.
class ScrollingElement {
    // jqElement: the jQuery element to scroll. This may include
    // an actaul scrollable bar.
    // jqMenuItems: the jQuery element that contains the menu items.
    constructor(jqElement, jqMenuItemsContainer) {
        this.jqElement = jqElement;
        this.jqMenuItemsContainer = jqMenuItemsContainer;
        this.speedDeterminator = new SpeedDeterminator(SPEED_SAMPLE_SPAN_MILLIS);
        this.startPosition = -1;
        this.startScrollLeft = -1;
        this.absoluteMovement = 0;
        this.currentPosition = -1;
        this.inertialStartPosition = -1;
        this.inertialSpeedPxPerSec = -1;
        this.inertialInterpolator = null;
        this.doingIntertialAnimation = false;
        this.wasClick = false;
        this.elasticElements = null;
        this.elasticElementWidth = 0;
        this.elasticElementIndex = 0;

        // The bound function that was last used for a requestAnimationFrame callback.
        this.lastAnimateCallbackFunction = null;

        // Collection of bound functions.
        this.boundFunctions = {
            onMouseDown: this.onMouseDown.bind(this),
            onMouseMove: this.onMouseMove.bind(this),
            onMouseUp: this.onMouseUp.bind(this),
            inertialAnimate: this.makeAnimatorBinding(this.inertialAnimate),
            scrollAnimator: this.makeAnimatorBinding(this.scrollAnimator)
        };

        // Binds the mouse down event to the scrolling element.
        jqMenuItemsContainer.on('mousedown', this.boundFunctions.onMouseDown);
    }

    setElasticElements(leftElaticElement, rightElaticElement) {
        this.elasticElements = [leftElaticElement, rightElaticElement];
        const containerHeight = this.jqMenuItemsContainer.height();
        const borderHeightTotal = getCssSize(leftElaticElement, CSS_BORDER_HEIGHT_PROPOERTIES);
        const elasticHeight = containerHeight - borderHeightTotal;
        const style = { width: 0, height: elasticHeight};
        leftElaticElement.css(style);
        rightElaticElement.css(style)
    }

    // Adds a sample value to the speed determinator.
    addSample(event) {
        this.speedDeterminator.addSample(new TimedSampleClientXEvent(event));
    }

    // Sets the current animation callback function. Cancels the previous
    // animation callback function if it was different.
    setAnimator(animator) {
        if (this.lastAnimateCallbackFunction == animator) {
            return;
        }
        if (this.lastAnimateCallbackFunction != null) {
            cancelAnimationFrame(this.lastAnimateCallbackFunction);
        }
        requestAnimationFrame(animator);
        this.lastAnimateCallbackFunction = animator;
    }

    // Cancels the current animation callback function.
    cancelAnimator() {
        if (this.lastAnimateCallbackFunction != null) {
            cancelAnimationFrame(this.lastAnimateCallbackFunction);
            this.clearAnimator();
        }
    }

    // Clears the lastAnimateCallbackFunction member variable.
    clearAnimator() {
        this.lastAnimateCallbackFunction = null;
    }

    // Member function used for functions used with requestAnimationFrame.
    // This will clear the lastAnimateCallbackFunction member variable
    // as on callback and then call the requested animator function.
    // Note: use setAnimator() to call requestAnimationFrame.
    makeAnimatorBinding(animator) {
        const boundClearAnimator =this.clearAnimator.bind(this);
        const boundAnimator = animator.bind(this);
        return function () {
            boundClearAnimator();
            boundAnimator();
        };
    }

    // To be called whenever the mouse is pressed on the scrolling element.
    onMouseDown(event) {
        this.addSample(event);
        this.startPosition = event.clientX;
        this.startScrollLeft = this.jqElement.scrollLeft();
        this.absoluteMovement = 0;
        this.cancelAnimator(); // Stops interial scrolling if any.


        // Grabs mouse move and up events on the whole document.
        $(document).on('mousemove', this.boundFunctions.onMouseMove);
        $(document).on('mouseup', this.boundFunctions.onMouseUp);
    }

    // To be called whenever the mouse is released.
    onMouseUp(event) {
        this.cancelAnimator(); // Stops any prior scroll animations.
        this.addSample(event);
        this.currentPosition = event.clientX;
        this.wasClick = this.absoluteMovement < MIN_PX_FOR_CLICK_EVENT;
        $(document).off('mousemove', this.boundFunctions.onMouseMove);
        $(document).off('mouseup', this.boundFunctions.onMouseUp);
        this.startInertialAnimation();
    }

    // Called to start the animation of inertial scrolling.
    startInertialAnimation() {
        const speedPxPerSec = this.speedDeterminator.getSpeed() * 1000;

        if (Math.abs(speedPxPerSec) < MIN_SPEED_FOR_INTERIA_PX_PER_SEC
            && !(this.elasticElementWidth > 0)) {
            return;
        }

        this.inertialStartPosition = this.currentPosition;
        this.inertialSpeedPxPerSec = speedPxPerSec;
        this.inertialInterpolator = new TimedDecay(INERTIA_ANIMATION_DURATION_MILLIS);
        this.doingIntertialAnimation = true;

        this.setAnimator(this.boundFunctions.inertialAnimate);
    }

    // Called to animate the inertial scrolling once the mouse has been released.
    inertialAnimate() {
        const interpValue = this.inertialInterpolator.getFactor();
        if (interpValue <= 0.0) {
            // Scroll is done.
            this.doingIntertialAnimation = false;
            this.stretchElastic(0, 0);
            return;
        }

        // If there is a stretch elastic element, then release it.
        if (this.elasticElementWidth > 0) {
            this.stretchElastic(
                this.elasticElementWidth * interpValue,
                this.elasticElementIndex);
        }

        const scaler = interpValue  * interpValue * interpValue;

        this.currentPosition = this.inertialStartPosition +
            (1 - scaler) * this.inertialSpeedPxPerSec;

        // Moves scroll position based on current position.
        this.scrollAnimator();
        // Reschedule this callback function.
        this.setAnimator(this.boundFunctions.inertialAnimate);
    }

    // Called on mouse moves.
    // This frequency of this callback can vary wildly depending on the
    // browser, the mouse device and even if jit is enabled. Hence the
    // use of requestAnimationFrame (see setAnimator).
    onMouseMove(event) {
        this.addSample(event);
        event.preventDefault();
        event.stopPropagation();
        this.absoluteMovement += Math.abs(event.clientX - this.currentPosition);
        this.currentPosition = event.clientX;
        this.setAnimator(this.boundFunctions.scrollAnimator);
    }

    // Returns true if the elastic element at index is stretched.
    isStretched(index) {
        return this.elasticElementWidth > 0 && this.elasticElementIndex == index;
    }

    // Stretch the elastic element by amount on the side of index.
    // The amount will be modulated between 0 and MAX_ELASTIC_WIDTH
    // for any value of amount.
    stretchElastic(amount, index) {
        if (this.elasticElements == null) {
            return;  // Nothing to stretch.
        }
        const stretchElem = this.elasticElements[index];
        const otherElem = this.elasticElements[index ? 0 : 1];
        if (amount <= 0) {
            // We don't stretch negative amounts.
            this.elasticElementWidth = 0;
            stretchElem.width(0);
            otherElem.width(0);
            return;
        }
        this.elasticElementWidth = amount;
        this.elasticElementIndex = index;

        const factor = amount / MAX_ELASTIC_WIDTH;
        const scale = factor / (1 + factor);
        stretchElem.width(MAX_ELASTIC_WIDTH * scale)
        otherElem.width(0);
    }

    scrollAnimator() {
        const jthis = this.jqElement;
        const distance = this.currentPosition - this.startPosition;

        // Update current position based on swipe distance and sensitivity
        var currentPos = this.startScrollLeft - distance / 1;

        // Set boundaries for swiper
        const maxPos = jthis.prop('scrollWidth') - jthis.width();

        // Snap to boundaries if outside of bounds
        if (currentPos < this.elasticElementWidth) {
            if (!this.doingIntertialAnimation) {
                this.stretchElastic(-currentPos, 0);
            }
            currentPos = 0;
        } else if (currentPos > maxPos) {
            if (!this.doingIntertialAnimation) {
                this.stretchElastic(currentPos - maxPos, 1);
            }
            currentPos = maxPos;
        }

        // Update swiper position
        jthis.scrollLeft(currentPos);
        this.updateViews();
    }

    updateViews() {
        // override this.
    }
}

const CSS_BORDER_WIDTH_PROPERTIES = [ 'border-left-width', 'border-right-width' ];
const CSS_BORDER_HEIGHT_PROPOERTIES = [ 'border-top-width', 'border-bottom-width' ];
const CHEVRON_SIZE_FACTOR = 1.0 / 4.0;

function parseCssSize(cssSize) {
    if (cssSize == null) {
        return 0;
    }
    return parseFloat(cssSize);
}

function getCssSize(jqElement, cssProperties) {
    var size = 0;
    for (var i = 0; i < cssProperties.length; i++) {
        size += parseCssSize(jqElement.css(cssProperties[i]));
    }
    return size;
}

    
// A ScrollingElement that controls chevrons at the ends of the
// scrolling container.
class ScrollingChevronElement extends ScrollingElement {
    // jqChevronLeft: jQuery element for the left chevron.
    // jqChevronRight: jQuery element for the right chevron.
    constructor(jqElement, jqMenuItemsContainer, jqMenuItems, jqChevronLeft, jqChevronRight) {
        super(jqElement, jqMenuItemsContainer);
        this.jqMenuItems = jqMenuItems;
        this.jqChevronLeft = jqChevronLeft;
        this.jqChevronRight = jqChevronRight;
        const boundFunctions = this.boundFunctions;
        boundFunctions.updateChevrons = this.updateChevrons.bind(this);
        boundFunctions.onChevronLeftClick = this.onChevronLeftClick.bind(this);
        boundFunctions.onChevronRightClick = this.onChevronRightClick.bind(this);
        boundFunctions.onChevronMouseDown = this.onChevronMouseDown.bind(this);
        requestAnimationFrame(boundFunctions.updateChevrons);
        
        $(window).resize(this.boundUpdateChevrons);
        this.jqChevronLeft.click(boundFunctions.onChevronLeftClick);
        this.jqChevronRight.click(boundFunctions.onChevronRightClick);

        this.jqChevronLeft.mousedown(boundFunctions.onChevronMouseDown);
        this.jqChevronRight.mousedown(boundFunctions.onChevronMouseDown);
    }

    // Updates the chevron visibility based on the current scroll 
    // position.
    updateChevrons() {
        // Get border size for the chevron. This assumes the border is the same
        // on both sides.
        const borderWidthTotal = getCssSize(this.jqChevronLeft, CSS_BORDER_WIDTH_PROPERTIES);
        const borderHeightTotal = getCssSize(this.jqChevronLeft, CSS_BORDER_HEIGHT_PROPOERTIES);
 
        const containerHeight = this.jqMenuItemsContainer.height();
        const containerWidth = this.jqMenuItemsContainer.width();
        const scrollerOffset = this.jqElement.offset();
        const menuItemWidth = this.jqMenuItems.width();

        const chevronWidth = menuItemWidth * CHEVRON_SIZE_FACTOR;
        
        const jthis = this.jqElement;
        const currentScrollPos = jthis.scrollLeft();
        const maxPos = this.jqElement.prop('scrollWidth') - this.jqElement.width();

        if (currentScrollPos <= 0 || this.isStretched(0)) {
            this.jqChevronLeft.css({display: 'none'});
        } else {
            this.jqChevronLeft.css({
                position: 'absolute',
                top: scrollerOffset.top,
                left: scrollerOffset.left,
                display: 'block',
                height: containerHeight - borderHeightTotal,
                width: chevronWidth - borderWidthTotal,
            });
        }
        
        if (currentScrollPos >= (maxPos - 2) || this.isStretched(1)) {
            this.jqChevronRight.css({display: 'none'});
        } else {
            this.jqChevronRight.css({
                position: 'absolute',
                top: scrollerOffset.top,
                left: scrollerOffset.left + containerWidth - chevronWidth,
                display: 'block',
                height: containerHeight - borderHeightTotal,
                width: chevronWidth - borderWidthTotal,
            });
        }
    }

    performScroll(scrollSize) {
        const seconds = INERTIA_ANIMATION_DURATION_MILLIS / 1000.0;

        this.startScrollLeft = this.jqElement.scrollLeft();
        if (this.doingIntertialAnimation) {
            this.inertialSpeedPxPerSec = 1.5 * scrollSize / seconds;
        } else {
            this.inertialSpeedPxPerSec = scrollSize / seconds;
        }
        this.inertialStartPosition = this.jqElement.scrollLeft();
        
        this.startPosition = this.inertialStartPosition;
        this.inertialInterpolator = new TimedDecay(INERTIA_ANIMATION_DURATION_MILLIS);
        this.doingIntertialAnimation = true;

        this.setAnimator(this.boundFunctions.inertialAnimate);

    }

    // Called when the left chevron is clicked.
    onChevronLeftClick() {
        const scrollSize = this.jqMenuItems.width();
        this.performScroll(scrollSize);
    }

    // Called when the right chevron is clicked.
    onChevronRightClick() {
        const scrollSize = this.jqMenuItems.width();
        this.performScroll(-scrollSize);
    }

    // Updates the chevron views.
    updateViews() {
        super.updateViews();
        requestAnimationFrame(this.boundFunctions.updateChevrons);
    }

    // Prevents scrolling when the chevron is clicked.
    onChevronMouseDown(event) {
        event.stopPropagation();
    }
}
