

// Constructor for timed sample values.
class TimedSampleValue {
    constructor(value, timestampMillis) {
        this.value = value;
        this.timestampMillis = timestampMillis;
    }
}

class TimedSampleClientXEvent extends TimedSampleValue {
    constructor(event) {
        super(getClientXPosition(event), performance.now());
    }
}

// Constructor for SpeedDeterminator object.
// The speed determinator is used to determine the speed of the
// mouse pointer in pixels since some given time in the past.
class SpeedDeterminator {
    constructor(spanMillis) {
        this.spanMillis = spanMillis;
        this.initialSample = null;
        this.samples = [];
    }

    reset() {
        this.initialSample = null;
        this.samples = [];
    }

    // Adds a new sample value.
    addSample(sampleValue) {
        if (sampleValue.value == null) {
            return;
        }
        if (this.initialSample == null) {
            this.initialSample = sampleValue;
        }
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
    getSpeed() {
        return this.getSpeedAt(performance.now());
    }

    getSpeedAt(timestampMillis) {
        if (this.samples.length < 2) {
            return 0;
        }
        const sampleA = this.samples[0];
        const sampleB = this.samples[this.samples.length - 1];
        var elapsedMillis;
        if (timestampMillis != null) {
            elapsedMillis = timestampMillis - sampleA.timestampMillis;
        } else {
            elapsedMillis = sampleB.timestampMillis - sampleA.timestampMillis;
        }
        if (elapsedMillis <= 0) {
            return 0;
        }
        const distance = sampleB.value - sampleA.value;
        return distance / elapsedMillis;
    }

    direction() {
        const speed = this.getSpeed();
        if (speed != 0) {
            return Math.sign(speed);
        }
        if (this.samples.length < 2) {
            return 0;
        }
        const lastSample = this.samples[this.samples.length - 1];
        return Math.sign(lastSample.value - this.initialSample.value);
    }
}

function deepMerge(options, defaultValues) {
    // Create a new object to store the merged properties
    let merged = {};
    
    for (let key of Object.keys(defaultValues)) {
        if (typeof defaultValues[key] == "function") {
            // If the property is a function, use it as is.
            if (!options[key]) {
                merged[key] = defaultValues[key];
            } else {
                merged[key] = options[key];
            }
        } else if (defaultValues[key] instanceof Object) {
            if (!options[key]) {
                // If the property doesn't exist in the target object,
                // just copy the value from the source object
                merged[key] = { ...defaultValues[key] };
            } else {
                // Recursively merge the nested properties
                merged[key] = deepMerge(options[key], defaultValues[key]);
            }
        } else {
            if (!options[key]) {
                merged[key] = defaultValues[key];
            } else {
                merged[key] = options[key];
            }
        }
    }
    
    // Return the merged object
    return merged;
}

// Returns an ordered set of offsets for the menu items.
function defaultSnapToResolver(scroller) {
    const menuItems = scroller.jqMenuItems;
    return $.map(menuItems, function(element) {
        const offset = $(element).offset();
        return {
            top: offset.top,
            left: offset.left,
            right: offset.left + $(element).outerWidth(),
            bottom: offset.top + $(element).outerHeight(),
        };
    }).sort(function(a, b) {
        return a.left - b.left;
    });
}
  
var STACK_SAMPLES = [];

const SPEED_SAMPLE_SPAN_MILLIS = 500;
const MIN_SPEED_FOR_INTERIA_PX_PER_SEC = 10;
const INERTIA_ANIMATION_DURATION_MILLIS = 500;
const ELASTIC_ANIMATION_DURATION_MILLIS = 400;
const MIN_PX_FOR_CLICK_EVENT = 5;
const MAX_ELASTIC_WIDTH = 200;
const CHEVRON_SIZE_FACTOR = 1.0 / 4.0;
const DATA_IDENTIFIER_FOR_SCROLLING_ELEMENT = "scrollingElement";
const INERTIA_SPEED_FACTOR = 0.75;

// Default parameters for the scrolling element.
const SCROLLING_ELEMENT_PARAMERTERS = {
    speedSampleSpanMillis: SPEED_SAMPLE_SPAN_MILLIS,
    minSpeedForInteriaPxPerSec: MIN_SPEED_FOR_INTERIA_PX_PER_SEC,
    inertiaAnimationDurationMillis: INERTIA_ANIMATION_DURATION_MILLIS,
    elasticAnimationDurationMillis: ELASTIC_ANIMATION_DURATION_MILLIS,
    minPxForClickEvent: MIN_PX_FOR_CLICK_EVENT,
    maxElasticWidth: MAX_ELASTIC_WIDTH,
    chevronSizeFactor: CHEVRON_SIZE_FACTOR,
    dataIdentifierForScrollingElement: DATA_IDENTIFIER_FOR_SCROLLING_ELEMENT,
    snapToItemsOffsetsFunction: defaultSnapToResolver,
    inertiaSpeedFactor: INERTIA_SPEED_FACTOR,
};

function scrollingElementParameters(options) {
    if (options) {
        return deepMerge(options, SCROLLING_ELEMENT_PARAMERTERS);
        // var copy = { ...SCROLLING_ELEMENT_PARAMERTERS };
        // return Object.assign(copy, options);
    }
    return SCROLLING_ELEMENT_PARAMERTERS;
}


// Grabs the X position from an event.
function getClientXPosition(eventValue) {
    if (eventValue.type.startsWith('mouse')) {
        return eventValue.clientX;
    } else if (eventValue.type == 'touchstart' || eventValue.type == 'touchend') {
        return null;
    } else if (eventValue.type.startsWith('touch')){
        return eventValue.originalEvent.touches[0].clientX;
    }
    throw new Error('Unsupported event type: ' + eventValue.type);
}

const EPSILONPX = 0.1;
const LARGE_EPSILONPX = 1.0;

// Constructor function for a scrolling object.
class ScrollingElement {
    // jqElement: the jQuery element to scroll. This may include
    // an actaul scrollable bar.
    // jqMenuItems: the jQuery element that contains the menu items.
    constructor(jqElement, jqMenuItemsContainer, jqMenuItems, params) {
        this.params = scrollingElementParameters(params);
        this.jqElement = jqElement;
        this.jqMenuItemsContainer = jqMenuItemsContainer;
        this.jqMenuItems = jqMenuItems;
        this.speedDeterminator = new SpeedDeterminator(this.params.speedSampleSpanMillis);
        this.startPosition = -1;
        this.startScrollLeft = -1;
        this.absoluteMovement = 0;
        this.currentPosition = -1;
        this.inertialStartPosition = -1;
        this.inertialFinalOffset = -1;
        this.inertialInterpolator = null;
        this.doingIntertialAnimation = false;
        this.inertialElasticElementWidth = 0;
        this.wasClick = false;
        this.elasticElements = null;
        this.elasticElementWidth = 0;
        this.elasticElementIndex = 0;
        this.snapToPositionDisabled = false;

        // The bound function that was last used for a requestAnimationFrame callback.
        this.lastAnimateCallbackFunction = null;

        // Collection of bound functions.
        this.boundFunctions = {
            onMouseDown: this.onMouseDown.bind(this),
            onMouseMove: this.onMouseMove.bind(this),
            onMouseUp: this.onMouseUp.bind(this),
            updateViews: this.updateViews.bind(this),
            inertialAnimate: this.makeAnimatorBinding(this.inertialAnimate),
            scrollAnimator: this.makeAnimatorBinding(this.scrollAnimator)
        };

        // Binds the mouse down event to the scrolling element.
        jqMenuItemsContainer.on('mousedown', this.boundFunctions.onMouseDown);
        jqMenuItemsContainer.on('touchstart', this.boundFunctions.onMouseDown);
        
        $(window).resize(this.boundFunctions.updateViews);
    }

    setElasticElements(leftElaticElement, rightElaticElement, fillerElement) {
        this.elasticElements = [leftElaticElement, rightElaticElement, fillerElement];
        this.updateOnResize();
    }

    updateOnResize() {
        if (this.elasticElements != null) {
            const leftElaticElement = this.elasticElements[0];
            const rightElaticElement = this.elasticElements[1];
            const containerHeight = this.jqMenuItems.outerHeight(true);
            const borderHeightTotal = getCssSize(leftElaticElement, CSS_BORDER_HEIGHT_PROPOERTIES);
            const elasticHeight = containerHeight - borderHeightTotal;
            const style = {height: elasticHeight};
            leftElaticElement.css(style);
            rightElaticElement.css(style)
            // find the rightmost menu item.
            const rightmostItem = this.jqMenuItems.last();
            const rightmostItemRight = rightmostItem.offset().left + rightmostItem.outerWidth(true);
            const containerRight = this.jqMenuItemsContainer.offset().left + this.jqMenuItemsContainer.outerWidth(true);
            const fillerWidth = containerRight - rightmostItemRight;
            if (fillerWidth < 0) {
                this.elasticElements[2].hide();
                this.snapToPositionDisabled = false;
            } else {
                this.snapToPositionDisabled = true;
                this.elasticElements[2].show();
                this.elasticElements[2].css({width: fillerWidth});
            }
        }
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
        this.speedDeterminator.reset();
        this.addSample(event);
        this.startPosition = getClientXPosition(event);
        this.startScrollLeft = this.jqElement.scrollLeft();
        this.absoluteMovement = 0;
        this.cancelAnimator(); // Stops interial scrolling if any.
        this.doingIntertialAnimation = false;

        // Grabs mouse move and up events on the whole document.
        $(document).bind(
            'mousemove touchmove', 
            this.boundFunctions.onMouseMove);
        $(document).bind(
            'mouseup touchend',
            this.boundFunctions.onMouseUp);
    }

    // To be called whenever the mouse is released.
    onMouseUp(event) {
        this.cancelAnimator(); // Stops any prior scroll animations.
        this.addSample(event);
        this.wasClick = this.absoluteMovement < this.params.minPxForClickEvent;
        $(document).unbind('mousemove touchmove', this.boundFunctions.onMouseMove);
        $(document).unbind('mouseup touchend', this.boundFunctions.onMouseUp);
        this.startInertialAnimation();
    }

    maybeFindSnapPositions() {
        if (this.params.snapToItemsOffsetsFunction) {
            return this.params.snapToItemsOffsetsFunction(this);
        }
        return null;
    }

    findNextSnapPosition(scrollerLeftSide, scrollerRightSide, snapOffsets) {
        if (snapOffsets.length <= 1) {
            return 0;
        }
        // If the first snapOffset is greater than the current position, then
        // then snap use the first snapOffset.
        if (snapOffsets[1].left + EPSILONPX >= scrollerLeftSide) {
            return 0;
        }
        // If the last snapOffset is less than the current position, then
        // then snap use the last snapOffset.
        const last = snapOffsets[snapOffsets.length - 1];
        if (last.right - LARGE_EPSILONPX <= scrollerRightSide) {
            return snapOffsets.length - 1;
        }
        // Find the first snapOffset whose left is less than the current position.
        for (let i = 1; i < snapOffsets.length; i++) {
            const snapOffsetPrev = snapOffsets[i - 1];
            const snapOffset = snapOffsets[i];
            if (snapOffsetPrev.right - EPSILONPX <= scrollerLeftSide && snapOffset.right + EPSILONPX >= scrollerLeftSide) {
                return i;
            }
        }
        return snapOffsets.length - 1;
    }

    findIntertialFinalOffset() {
        const proposedOffset = this.speedDeterminator.getSpeed() * 1000 * this.params.inertiaSpeedFactor;
        return this.findIntertialFinalOffsetFor(
            proposedOffset, this.speedDeterminator.direction());
    }

    findIntertialFinalOffsetFor(proposedOffset, direction) {
        const snapPositions = this.maybeFindSnapPositions();
        if (snapPositions == null 
            || snapPositions.length < 2 
            || this.snapToPositionDisabled) {

            if (Math.abs(proposedOffset) < this.params.minSpeedForInteriaPxPerSec
                && !(this.elasticElementWidth > 0)) {
                return 0;
            }
            return proposedOffset + this.elasticElementWidth;
        }

        const elsaticCorrection = 
            this.elasticElementIndex == 0 
            ? this.elasticElementWidth : -this.elasticElementWidth;
        
        var scrollerLeftSide = this.jqElement.offset().left + elsaticCorrection;
        var scrollerRightSide = scrollerLeftSide + this.jqElement.width();
        const nextSnapPositionIndex = this.findNextSnapPosition(
            scrollerLeftSide - proposedOffset, 
            scrollerRightSide - proposedOffset,
            snapPositions);
        

        if (direction >= 0 && !Math.abs(proposedOffset) < this.params.minSpeedForInteriaPxPerSec) {
            return scrollerLeftSide - snapPositions[nextSnapPositionIndex].left;
        }
        if (nextSnapPositionIndex == snapPositions.length - 1) {
            return scrollerLeftSide - snapPositions[nextSnapPositionIndex].right;
        }
        return scrollerLeftSide - snapPositions[nextSnapPositionIndex + 1].left;
    }

    // Called to start the animation of inertial scrolling.
    startInertialAnimation() {
        const inertialFinalOffset = this.findIntertialFinalOffset();
        this.startAnimationForOffset(inertialFinalOffset);
    }

    startAnimationForOffset(inertialFinalOffset) {
        if (inertialFinalOffset == 0) {
            return;
        }

        this.inertialFinalOffset = inertialFinalOffset;
        this.startScrollLeft = this.jqElement.scrollLeft();
        this.inertialStartPosition = this.currentPosition;
        this.doingIntertialAnimation = true;
        this.inertialElasticElementWidth = this.elasticElementWidth;

        const animationTimeMillis = 
            this.inertialElasticElementWidth > 0 
            ? this.params.elasticAnimationDurationMillis
            : this.params.inertiaAnimationDurationMillis;

        this.inertialInterpolator = new TimedDecay(animationTimeMillis);
        this.setAnimator(this.boundFunctions.inertialAnimate);
    }

    // Called to animate the inertial scrolling once the mouse has been released.
    inertialAnimate() {
        const interpValue = this.inertialInterpolator.getFactor();
        if (interpValue <= 0.0 || !this.doingIntertialAnimation) {
            // Scroll is done.
            this.doingIntertialAnimation = false;
            this.inertialElasticElementWidth = 0;
            this.stretchElastic(0, 0);
            return;
        }

        // Cubic interpolation. Starts fast and slows down towards the end.
        const scaler = interpValue * interpValue * interpValue;

        // If there is a stretch elastic element, then release it.
        if (this.inertialElasticElementWidth > 0) {
            this.stretchElastic(
                this.inertialElasticElementWidth * scaler,
                this.elasticElementIndex);
        }
        const distance = (1 - scaler) * this.inertialFinalOffset;

        this.scrollBy(distance);
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
        var currentPosition = getClientXPosition(event);
        if (this.startPosition == null) {
            this.startPosition = currentPosition;
        }
        this.absoluteMovement += Math.abs(currentPosition - this.currentPosition);
        this.currentPosition = currentPosition;
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

        const factor = amount / this.params.maxElasticWidth;
        // x/(1+x) is a sigmoid function that goes from 0 to 1 for x from 0 to infinity.
        // This is used to modulate the amount of stretch and makes it look more natural.
        const scale = factor / (1 + factor);
        stretchElem.width(this.params.maxElasticWidth * scale);
        otherElem.width(0);
    }

    
    scrollAnimator() {
        const distance = this.currentPosition - this.startPosition;
        this.scrollBy(distance);
    }

    scrollBy(distance) {
        
        // var stack = {};
        // Error.captureStackTrace(stack);
        // STACK_SAMPLES.push(stack);
        // console.log("scrollBy " + distance);
        // if (Math.abs(this.lastDistance - distance) > 20 && STACK_SAMPLES.length > 2) {
        //     console.log("scrollBy different " + Math.abs(this.lastDistance - distance));
        //     console.log(STACK_SAMPLES[STACK_SAMPLES.length - 2].stack);
        //     console.log("this frame's stack:");
        //     console.log(STACK_SAMPLES[STACK_SAMPLES.length - 1].stack);
        // }
        // this.lastDistance = distance;

        const jthis = this.jqElement;

        // Update current position based on swipe distance and sensitivity
        var newScrollPos = this.startScrollLeft - distance;

        // Set boundaries for swiper
        const maxPos = jthis.prop('scrollWidth') - jthis.width();

        // Snap to boundaries if outside of bounds
        if (newScrollPos < this.elasticElementWidth) {
            if (!this.doingIntertialAnimation) {
                this.stretchElastic(-newScrollPos, 0);
            }
            newScrollPos = 0;
        } else if (newScrollPos > maxPos) {
            if (!this.doingIntertialAnimation) {
                this.stretchElastic(newScrollPos - maxPos, 1);
            }
            newScrollPos = maxPos;
        } else if (this.inertialElasticElementWidth > 0) {
            if (this.elasticElementIndex == 1) {
                newScrollPos = maxPos;
            }
        }

        // Update swiper position
        jthis.scrollLeft(newScrollPos);
        this.updateViews();
    }

    updateViews() {
        this.updateOnResize();
    }
}

const CSS_BORDER_WIDTH_PROPERTIES = [ 'border-left-width', 'border-right-width' ];
const CSS_BORDER_HEIGHT_PROPOERTIES = [ 'border-top-width', 'border-bottom-width' ];

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
    constructor(jqElement, jqMenuItemsContainer, jqMenuItems, jqChevronLeft, jqChevronRight, params) {
        super(jqElement, jqMenuItemsContainer, jqMenuItems, params);
        this.jqChevronLeft = jqChevronLeft;
        this.jqChevronRight = jqChevronRight;
        const boundFunctions = this.boundFunctions;
        boundFunctions.updateChevrons = this.updateChevrons.bind(this);
        boundFunctions.onChevronLeftClick = this.onChevronLeftClick.bind(this);
        boundFunctions.onChevronRightClick = this.onChevronRightClick.bind(this);
        boundFunctions.onChevronMouseDown = this.onChevronMouseDown.bind(this);
        requestAnimationFrame(boundFunctions.updateChevrons);
        
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
 
        const containerHeight = this.jqMenuItems.outerHeight(true);
        const containerWidth = this.jqMenuItemsContainer.width();
        const scrollerOffset = this.jqElement.offset();
        const menuItemWidth = this.jqMenuItems.width();

        const chevronWidth = menuItemWidth * this.params.chevronSizeFactor;
        
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
        const offset = this.findIntertialFinalOffsetFor(scrollSize, Math.sign(scrollSize));
        this.startAnimationForOffset(offset)
        // const seconds = this.params.inertiaAnimationDurationMillis / 1000.0;

        // if (this.doingIntertialAnimation) {
        //     this.inertialFinalOffset = 1.5 * scrollSize / seconds;
        // } else {
        //     this.inertialFinalOffset = scrollSize / seconds;
        // }
        // const jthis = this.jqElement;
        // const maxPos = jthis.prop('scrollWidth') - jthis.width();
        // this.startScrollLeft = this.jqElement.scrollLeft();
        // const finalPos = this.startScrollLeft - this.inertialFinalOffset;
        // if ( finalPos < 0) {
        //     this.inertialFinalOffset += finalPos;
        // } else if (finalPos > maxPos) {
        //     this.inertialFinalOffset -= finalPos - maxPos;
        // }
        // this.inertialStartPosition = this.startScrollLeft + this.inertialFinalOffset;
        // this.inertialInterpolator = new TimedDecay(this.params.inertiaAnimationDurationMillis);
        // this.doingIntertialAnimation = true;
        // this.inertialElasticElementWidth = 0;

        // this.setAnimator(this.boundFunctions.inertialAnimate);
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

function translateToJqElement(element) {
    var jqElement = null;
    if (typeof element === 'string') {
        jqElement = $(element);
    } else {
        jqElement = element;
    }
    // Verify the element is valid jquery object.
    if (jqElement?.length === 0) {
        //throw 'Invalid element';
    }
    return jqElement;
}

// Builder for the ScrollingElement class.
class ScrollingElementBuilder {
    constructor() {
        this.params = {};
    }

    setParams(params) {
        this.params = params;
        return this;
    }

    setScrollingElement(scrollingElement) {
        this.scrollingElement = translateToJqElement(scrollingElement);
        return this;
    }

    setMenuItemsContainer(menuItemsContainer) {
        this.menuItemsContainer = translateToJqElement(menuItemsContainer);
        return this;
    }
    
    setMenuItems(menuItems) {     
        this.menuItems = translateToJqElement(menuItems);
        return this;
    }

    setChevronElements(chevronLeft, chevronRight) {
        this.chevronLeft = translateToJqElement(chevronLeft);
        this.chevronRight = translateToJqElement(chevronRight);
        return this;
    }

    setOverscrollElements(overscrollLeft, overscrollRight, overscrollFiller) {
        this.overscrollLeft = translateToJqElement(overscrollLeft);
        this.overscrollRight = translateToJqElement(overscrollRight);
        this.overscrollFiller = translateToJqElement(overscrollFiller);
        return this;
    }

    getDataIdentifier() {
        if (!this?.params?.dataIdentifierForScrollingElement) {
            return SCROLLING_ELEMENT_PARAMERTERS.dataIdentifierForScrollingElement;
        }
        return this.params.dataIdentifierForScrollingElement;
    }

    build() {
        // Make sure we have all the required elements.
        if (!this.scrollingElement) {
            throw 'Scrolling element not set';
        }

        if (!this.menuItemsContainer) {
            throw 'Menu items container not set';
        }

        if (!this.menuItems) {
            throw 'Menu items not set';
        }

        var result = null;
        if (!this.chevronLeft) {
            result = new ScrollingElement(
                this.scrollingElement, 
                this.menuItemsContainer,
                this.menuItems,
                this.params);
        } else {
            result = new ScrollingChevronElement(
                this.scrollingElement,
                this.menuItemsContainer,
                this.menuItems,
                this.chevronLeft,
                this.chevronRight,
                this.params);
        }

        if (this.overscrollLeft) {
            result.setElasticElements(
                this.overscrollLeft, this.overscrollRight, this.overscrollFiller);
        }

        const dataIdentifier = this.getDataIdentifier();
        if (this.scrollingElement.data(dataIdentifier)) {
            throw 'Scrolling element already has a ' 
                + dataIdentifier 
                + '/ScrollingElement associated with it';
        }

        this.scrollingElement.data(dataIdentifier, result);
        return result;
    }
}
